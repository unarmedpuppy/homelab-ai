"""
Unusual Whales Browser Session Manager
=======================================

Playwright-based browser automation for scraping Unusual Whales.
Handles authentication, session management, and page navigation.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from .config import get_settings, UWScraperSettings
from .cache import UWScraperCache
from .models import ScraperStatus, ScraperStatusCode, AuthCredentials

logger = logging.getLogger(__name__)


class UWBrowserSession:
    """
    Browser session manager for Unusual Whales scraping.

    Handles:
    - Playwright browser initialization
    - Authentication with username/password
    - Session cookie management
    - Page navigation with retry logic
    - Rate limiting between requests
    """

    def __init__(
        self,
        settings: Optional[UWScraperSettings] = None,
        cache: Optional[UWScraperCache] = None,
    ):
        """
        Initialize the browser session manager.

        Args:
            settings: Scraper settings. Uses global settings if not specified.
            cache: Cache instance for session persistence.
        """
        self.settings = settings or get_settings()
        self.cache = cache or UWScraperCache()

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        self._is_authenticated = False
        self._last_request_time: Optional[datetime] = None
        self._status = ScraperStatus()

    @property
    def is_authenticated(self) -> bool:
        """Check if session is authenticated"""
        return self._is_authenticated

    @property
    def status(self) -> ScraperStatus:
        """Get current scraper status"""
        return self._status

    async def start(self):
        """Start the browser session"""
        logger.info("Starting browser session...")

        try:
            # Initialize Playwright
            self._playwright = await async_playwright().start()

            # Launch browser
            self._browser = await self._playwright.chromium.launch(
                headless=self.settings.headless,
            )

            # Create browser context with custom user agent
            self._context = await self._browser.new_context(
                user_agent=self.settings.user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )

            # Set default timeouts
            self._context.set_default_timeout(self.settings.page_load_timeout)
            self._context.set_default_navigation_timeout(self.settings.navigation_timeout)

            # Create initial page
            self._page = await self._context.new_page()

            # Try to restore session from cache
            await self._restore_session()

            logger.info(
                f"Browser session started (headless={self.settings.headless}, "
                f"authenticated={self._is_authenticated})"
            )

        except Exception as e:
            logger.error(f"Failed to start browser session: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the browser session and clean up resources"""
        logger.info("Stopping browser session...")

        try:
            # Save session before closing
            if self._is_authenticated and self._context:
                await self._save_session()

            if self._page:
                await self._page.close()
                self._page = None

            if self._context:
                await self._context.close()
                self._context = None

            if self._browser:
                await self._browser.close()
                self._browser = None

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            logger.info("Browser session stopped")

        except Exception as e:
            logger.error(f"Error stopping browser session: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def _restore_session(self):
        """Try to restore session from cached cookies"""
        try:
            cookies = await self.cache.load_session()
            if cookies:
                await self._context.add_cookies(cookies)

                # Verify session is still valid
                await self._page.goto(self.settings.market_tide_url)
                await self._page.wait_for_load_state("networkidle")

                # Check if we're logged in (look for login button absence)
                login_button = await self._page.query_selector('a[href="/login"]')
                if login_button is None:
                    self._is_authenticated = True
                    self._status.is_authenticated = True
                    self._status.session_valid = True
                    logger.info("Session restored from cache")
                else:
                    logger.info("Cached session is no longer valid")
                    await self.cache.clear_session()

        except Exception as e:
            logger.warning(f"Failed to restore session: {e}")
            await self.cache.clear_session()

    async def _save_session(self):
        """Save current session cookies to cache"""
        try:
            cookies = await self._context.cookies()
            # Set expiry to 24 hours from now
            expiry = datetime.now() + timedelta(hours=24)
            await self.cache.save_session(cookies, expiry)
            logger.debug("Session cookies saved to cache")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    async def authenticate(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> bool:
        """
        Authenticate with Unusual Whales.

        Args:
            username: Login username (email). Uses settings if not specified.
            password: Login password. Uses settings if not specified.

        Returns:
            True if authentication successful, False otherwise.
        """
        username = username or self.settings.username
        password = password or self.settings.password

        if not username or not password:
            logger.error("No credentials provided for authentication")
            self._status.record_failure(
                ScraperStatusCode.AUTH_REQUIRED,
                "No credentials configured"
            )
            return False

        logger.info(f"Authenticating as {username}...")

        try:
            # Navigate to login page
            await self._page.goto(self.settings.login_url)
            await self._page.wait_for_load_state("networkidle")

            # Wait for login form
            await self._page.wait_for_selector('input[type="email"], input[name="email"]')

            # Fill in credentials
            # Try different possible selectors for email/username field
            email_input = await self._page.query_selector(
                'input[type="email"], input[name="email"], input[placeholder*="email" i]'
            )
            if email_input:
                await email_input.fill(username)
            else:
                logger.error("Could not find email input field")
                return False

            # Fill password
            password_input = await self._page.query_selector(
                'input[type="password"], input[name="password"]'
            )
            if password_input:
                await password_input.fill(password)
            else:
                logger.error("Could not find password input field")
                return False

            # Add random delay to appear more human-like
            await asyncio.sleep(random.uniform(0.5, 1.5))

            # Click login button
            login_button = await self._page.query_selector(
                'button[type="submit"], button:has-text("Log in"), button:has-text("Sign in")'
            )
            if login_button:
                await login_button.click()
            else:
                # Try pressing Enter instead
                await password_input.press("Enter")

            # Wait for navigation
            await self._page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)  # Extra wait for any redirects

            # Check if login was successful
            # Look for common indicators of being logged in
            current_url = self._page.url

            # Check if we're no longer on the login page
            if "/login" not in current_url.lower():
                self._is_authenticated = True
                self._status.is_authenticated = True
                self._status.session_valid = True
                await self._save_session()
                logger.info("Authentication successful")
                return True

            # Check for error messages
            error_element = await self._page.query_selector(
                '.error, .alert-danger, [role="alert"]'
            )
            if error_element:
                error_text = await error_element.inner_text()
                logger.error(f"Login failed: {error_text}")
                self._status.record_failure(
                    ScraperStatusCode.AUTH_FAILED,
                    f"Login failed: {error_text}"
                )
            else:
                logger.error("Login failed: Unknown reason")
                self._status.record_failure(
                    ScraperStatusCode.AUTH_FAILED,
                    "Login failed: Unknown reason"
                )

            # Take screenshot for debugging
            await self._take_error_screenshot("auth_failed")
            return False

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout during authentication: {e}")
            self._status.record_failure(ScraperStatusCode.TIMEOUT, str(e))
            await self._take_error_screenshot("auth_timeout")
            return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self._status.record_failure(ScraperStatusCode.AUTH_FAILED, str(e))
            await self._take_error_screenshot("auth_error")
            return False

    async def navigate(self, url: str, wait_for_selector: Optional[str] = None) -> bool:
        """
        Navigate to a URL with rate limiting and retry logic.

        Args:
            url: URL to navigate to
            wait_for_selector: Optional CSS selector to wait for after navigation

        Returns:
            True if navigation successful, False otherwise.
        """
        # Ensure rate limiting
        await self._enforce_rate_limit()

        for attempt in range(self.settings.max_retries):
            try:
                logger.debug(f"Navigating to {url} (attempt {attempt + 1})")

                await self._page.goto(url)
                await self._page.wait_for_load_state("networkidle")

                # Wait for specific selector if provided
                if wait_for_selector:
                    await self._page.wait_for_selector(wait_for_selector)

                # Add small random delay
                await asyncio.sleep(random.uniform(0.5, 1.5))

                self._last_request_time = datetime.now()
                logger.debug(f"Navigation successful: {url}")
                return True

            except PlaywrightTimeoutError as e:
                logger.warning(f"Navigation timeout (attempt {attempt + 1}): {e}")
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(self.settings.retry_delay * (attempt + 1))
                else:
                    self._status.record_failure(ScraperStatusCode.TIMEOUT, str(e))
                    await self._take_error_screenshot("navigation_timeout")
                    return False

            except Exception as e:
                logger.error(f"Navigation error (attempt {attempt + 1}): {e}")
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(self.settings.retry_delay * (attempt + 1))
                else:
                    self._status.record_failure(ScraperStatusCode.NETWORK_ERROR, str(e))
                    await self._take_error_screenshot("navigation_error")
                    return False

        return False

    async def _enforce_rate_limit(self):
        """Ensure minimum spacing between requests"""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            min_spacing = self.settings.min_request_spacing

            if elapsed < min_spacing:
                wait_time = min_spacing - elapsed
                # Add some jitter
                wait_time += random.uniform(0, 5)
                logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

    async def get_page_content(self) -> str:
        """Get the current page's HTML content"""
        return await self._page.content()

    async def get_page(self) -> Page:
        """Get the current Playwright page object for direct manipulation"""
        return self._page

    async def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript in the page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of the script execution
        """
        return await self._page.evaluate(script)

    async def wait_for_selector(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> bool:
        """
        Wait for a CSS selector to appear on the page.

        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds

        Returns:
            True if element found, False if timeout
        """
        try:
            await self._page.wait_for_selector(
                selector,
                timeout=timeout or self.settings.page_load_timeout
            )
            return True
        except PlaywrightTimeoutError:
            return False

    async def query_selector(self, selector: str):
        """Query for a single element matching the selector"""
        return await self._page.query_selector(selector)

    async def query_selector_all(self, selector: str) -> List:
        """Query for all elements matching the selector"""
        return await self._page.query_selector_all(selector)

    async def _take_error_screenshot(self, prefix: str):
        """Take a screenshot for debugging errors"""
        if not self.settings.screenshot_on_error:
            return

        try:
            self.settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.png"
            filepath = self.settings.screenshot_dir / filename

            await self._page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Error screenshot saved: {filepath}")

        except Exception as e:
            logger.error(f"Failed to save error screenshot: {e}")

    async def take_screenshot(self, name: str) -> Optional[Path]:
        """
        Take a screenshot of the current page.

        Args:
            name: Name for the screenshot file (without extension)

        Returns:
            Path to the saved screenshot, or None if failed
        """
        try:
            self.settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.settings.screenshot_dir / filename

            await self._page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Screenshot saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    async def ensure_authenticated(self) -> bool:
        """
        Ensure the session is authenticated.

        Attempts to authenticate if not already authenticated.

        Returns:
            True if authenticated, False otherwise.
        """
        if self._is_authenticated:
            return True

        if self.settings.has_credentials:
            return await self.authenticate()

        logger.warning("No credentials available for authentication")
        return False
