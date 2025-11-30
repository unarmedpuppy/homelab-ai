"""
Unusual Whales Browser Session Manager
=======================================

Playwright-based browser automation for scraping Unusual Whales.
Handles authentication, session management, and page navigation.
Uses stealth techniques to avoid bot detection.
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

try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    stealth_async = None

from .config import get_settings, UWScraperSettings
from .cache import UWScraperCache
from .models import ScraperStatus, ScraperStatusCode, AuthCredentials

logger = logging.getLogger(__name__)


# Stealth browser launch args to avoid detection
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--no-first-run",
    "--no-zygote",
    "--disable-gpu",
    "--hide-scrollbars",
    "--mute-audio",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-component-extensions-with-background-pages",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-features=TranslateUI",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--disable-sync",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--no-default-browser-check",
    "--password-store=basic",
    "--use-mock-keychain",
]


class UWBrowserSession:
    """
    Browser session manager for Unusual Whales scraping.

    Handles:
    - Playwright browser initialization with stealth mode
    - Authentication with username/password
    - Session cookie management
    - Page navigation with retry logic
    - Rate limiting between requests
    - Human-like behavior to avoid bot detection
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

    async def _human_delay(self, min_ms: int = 100, max_ms: int = 500):
        """Add a random human-like delay"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)

    async def _human_type(self, element, text: str, delay_range: tuple = (50, 150)):
        """Type text with human-like delays between keystrokes"""
        for char in text:
            await element.type(char, delay=random.randint(*delay_range))
            # Occasionally pause slightly longer
            if random.random() < 0.1:
                await self._human_delay(200, 500)

    async def _human_click(self, element):
        """Click with human-like behavior - move to element then click"""
        # Get element bounding box
        box = await element.bounding_box()
        if box:
            # Click at a random position within the element
            x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
            y = box["y"] + random.uniform(box["height"] * 0.2, box["height"] * 0.8)
            await self._page.mouse.click(x, y)
        else:
            await element.click()

    async def _apply_stealth_patches(self, page: Page):
        """Apply additional stealth patches via JavaScript"""
        # Override navigator.webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // Override plugins to look more realistic
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // Remove Playwright/Puppeteer artifacts
            delete window.__playwright;
            delete window.__PW_inspect;

            // Override Chrome runtime
            window.chrome = {
                runtime: {},
            };

            // Add missing WebGL fingerprint properties
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
        """)

    async def start(self):
        """Start the browser session with stealth mode"""
        logger.info("Starting browser session with stealth mode...")

        try:
            # Initialize Playwright
            self._playwright = await async_playwright().start()

            # Launch browser with stealth args
            self._browser = await self._playwright.chromium.launch(
                headless=self.settings.headless,
                args=STEALTH_ARGS,
            )

            # Create browser context with realistic settings
            self._context = await self._browser.new_context(
                user_agent=self.settings.user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                geolocation={"latitude": 40.7128, "longitude": -74.0060},
                permissions=["geolocation"],
                color_scheme="light",
                has_touch=False,
                is_mobile=False,
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                },
            )

            # Longer timeouts for bot-protected sites
            self._context.set_default_timeout(60000)  # 60 seconds
            self._context.set_default_navigation_timeout(90000)  # 90 seconds

            # Create initial page
            self._page = await self._context.new_page()

            # Apply stealth - use playwright-stealth if available
            if STEALTH_AVAILABLE:
                await stealth_async(self._page)
                logger.info("Applied playwright-stealth patches")
            else:
                logger.warning("playwright-stealth not available, using manual patches")

            # Apply additional manual stealth patches
            await self._apply_stealth_patches(self._page)

            # Try to restore session from cache
            await self._restore_session()

            logger.info(
                f"Browser session started (headless={self.settings.headless}, "
                f"stealth={'playwright-stealth' if STEALTH_AVAILABLE else 'manual'}, "
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

                # Add delay before navigation
                await self._human_delay(1000, 2000)

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
        Authenticate with Unusual Whales using human-like behavior.

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
            # Navigate to login page with human-like delay
            await self._human_delay(500, 1500)
            await self._page.goto(self.settings.login_url)
            await self._page.wait_for_load_state("networkidle")

            # Wait a bit after page load (like a human reading the page)
            await self._human_delay(1500, 3000)

            # Wait for login form - look for email field with various selectors
            await self._page.wait_for_selector(
                'input[placeholder*="address.com"], input[placeholder*="email" i], input[type="email"]',
                timeout=30000
            )

            # Find email input - try multiple possible selectors
            email_input = await self._page.query_selector(
                'input[placeholder*="address.com"], input[placeholder*="email" i], input[type="email"], input[name="email"]'
            )
            if not email_input:
                logger.error("Could not find email input field")
                await self._take_error_screenshot("auth_no_email_field")
                return False

            # Click on email field first (human behavior)
            await self._human_click(email_input)
            await self._human_delay(200, 500)

            # Type username with human-like delays
            await self._human_type(email_input, username)
            await self._human_delay(300, 800)

            # Find password input
            password_input = await self._page.query_selector(
                'input[type="password"], input[placeholder*="password" i], input[name="password"]'
            )
            if not password_input:
                logger.error("Could not find password input field")
                await self._take_error_screenshot("auth_no_password_field")
                return False

            # Click on password field
            await self._human_click(password_input)
            await self._human_delay(200, 500)

            # Type password with human-like delays
            await self._human_type(password_input, password)

            # Human-like pause before clicking login
            await self._human_delay(800, 2000)

            # Take a screenshot before submission for debugging
            await self._take_error_screenshot("before_submit")

            # Log what buttons we can find for debugging
            all_buttons = await self._page.query_selector_all('button')
            logger.info(f"Found {len(all_buttons)} buttons on page")
            for i, btn in enumerate(all_buttons):
                btn_text = await btn.inner_text()
                btn_type = await btn.get_attribute('type')
                logger.debug(f"  Button {i}: text='{btn_text}', type='{btn_type}'")

            # Try to click the Sign in button
            login_url = self._page.url
            logger.info("Attempting form submission")

            # Get button bounding box for precise mouse click
            sign_in_button = self._page.locator('button:has-text("Sign in")')
            await sign_in_button.wait_for(state='visible', timeout=10000)

            # Log button state
            is_visible = await sign_in_button.is_visible()
            is_enabled = await sign_in_button.is_enabled()
            box = await sign_in_button.bounding_box()
            logger.info(f"Button state: visible={is_visible}, enabled={is_enabled}, box={box}")

            # Method 1: Mouse click at exact coordinates with proper event sequence
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                logger.info(f"Clicking at coordinates ({x}, {y})")

                # Move mouse to button first (like a real user)
                await self._page.mouse.move(x, y)
                await self._human_delay(100, 200)

                # Perform full mouse click sequence
                await self._page.mouse.down()
                await self._human_delay(50, 100)
                await self._page.mouse.up()
                logger.info("Performed mouse down/up sequence")

            # Wait for navigation
            try:
                await self._page.wait_for_url(
                    lambda url: '/login' not in url.lower(),
                    timeout=10000
                )
                logger.info("Navigation detected after mouse click")
            except:
                logger.debug("No navigation after mouse click")

            await self._human_delay(1000, 2000)

            # Method 2: If still on login, try using keyboard navigation
            if "/login" in self._page.url.lower():
                logger.info("Trying Tab + Enter approach")
                try:
                    # Focus on password field, then Tab to button, then Enter
                    password_input = await self._page.query_selector('input[type="password"]')
                    if password_input:
                        await password_input.focus()
                        await self._human_delay(100, 200)
                        # Tab to the Sign in button
                        await self._page.keyboard.press("Tab")
                        await self._human_delay(100, 200)
                        # Press Enter or Space on the button
                        await self._page.keyboard.press("Enter")
                        logger.info("Tab + Enter pressed")

                        try:
                            await self._page.wait_for_url(
                                lambda url: '/login' not in url.lower(),
                                timeout=10000
                            )
                            logger.info("Navigation detected after Tab+Enter")
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"Tab+Enter approach failed: {e}")

            await self._human_delay(1000, 2000)

            # Method 3: Direct React event simulation
            if "/login" in self._page.url.lower():
                logger.info("Trying React synthetic event simulation")
                try:
                    # Find the button and trigger its onClick handler directly via React internals
                    result = await self._page.evaluate('''
                        () => {
                            const btn = document.querySelector('button');
                            if (!btn) return 'no button found';

                            // Find all buttons and look for Sign in
                            const buttons = Array.from(document.querySelectorAll('button'));
                            const signInBtn = buttons.find(b => b.innerText.toLowerCase().includes('sign in'));

                            if (!signInBtn) return 'no sign in button found';

                            // Create a proper MouseEvent
                            const mouseEvent = new MouseEvent('click', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                buttons: 1
                            });

                            signInBtn.dispatchEvent(mouseEvent);
                            return 'dispatched click event';
                        }
                    ''')
                    logger.info(f"React event simulation result: {result}")

                    try:
                        await self._page.wait_for_url(
                            lambda url: '/login' not in url.lower(),
                            timeout=10000
                        )
                    except:
                        pass
                except Exception as e:
                    logger.warning(f"React simulation failed: {e}")

            await self._human_delay(1000, 2000)

            # Method 4: Focus button and press Space (accessibility click)
            if "/login" in self._page.url.lower():
                logger.info("Trying focus + Space approach")
                try:
                    await sign_in_button.focus()
                    await self._human_delay(100, 200)
                    await self._page.keyboard.press("Space")
                    logger.info("Space pressed on focused button")

                    try:
                        await self._page.wait_for_url(
                            lambda url: '/login' not in url.lower(),
                            timeout=10000
                        )
                    except:
                        await self._page.wait_for_load_state("networkidle", timeout=5000)
                except Exception as e:
                    logger.warning(f"Focus+Space failed: {e}")

            await self._human_delay(1000, 2000)

            # Take screenshot after submission attempts
            await self._take_error_screenshot("after_submit")

            # Check if login was successful
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
                logger.error("Login failed: Unknown reason (possibly bot detection)")
                self._status.record_failure(
                    ScraperStatusCode.AUTH_FAILED,
                    "Login failed: Unknown reason (possibly bot detection)"
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

                # Human-like delay before navigation
                await self._human_delay(500, 1500)

                await self._page.goto(url)
                await self._page.wait_for_load_state("networkidle")

                # Wait for specific selector if provided
                if wait_for_selector:
                    await self._page.wait_for_selector(wait_for_selector, timeout=30000)

                # Human-like delay after page load
                await self._human_delay(1000, 2500)

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
                # Add some jitter for human-like behavior
                wait_time += random.uniform(2, 10)
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
