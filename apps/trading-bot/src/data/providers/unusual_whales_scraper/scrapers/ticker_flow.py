"""
Ticker Flow Scraper
===================

Scrapes per-ticker options flow data from Unusual Whales.

Target URL: https://unusualwhales.com/option-charts/ticker-flow?ticker_symbol={SYMBOL}
"""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..browser import UWBrowserSession
from ..models import TickerFlowData, ScraperStatusCode
from ..config import get_settings

logger = logging.getLogger(__name__)


class TickerFlowScraper:
    """
    Scraper for Unusual Whales per-ticker flow data.

    Extracts:
    - Net premium (calls vs puts)
    - Call/put volume
    - Premium distribution
    - Sentiment indicators
    """

    def __init__(self, browser: UWBrowserSession):
        """
        Initialize the ticker flow scraper.

        Args:
            browser: Browser session to use for scraping
        """
        self.browser = browser
        self.settings = get_settings()

    async def scrape(self, symbol: str) -> Optional[TickerFlowData]:
        """
        Scrape flow data for a specific ticker.

        Args:
            symbol: Ticker symbol (e.g., 'SPY', 'AAPL')

        Returns:
            TickerFlowData with extracted data, or None if failed.
        """
        symbol = symbol.upper()
        url = self.settings.ticker_flow_url(symbol)
        logger.info(f"Scraping ticker flow for {symbol} from {url}")

        try:
            # Ensure we're authenticated for full data
            is_authenticated = await self.browser.ensure_authenticated()

            # Navigate to the page
            success = await self.browser.navigate(url)
            if not success:
                logger.error(f"Failed to navigate to ticker flow page for {symbol}")
                return None

            # Wait for the page to fully render
            await self.browser.wait_for_selector(
                '[class*="chart"], [class*="flow"], [class*="ticker"], [data-testid]',
                timeout=15000
            )

            # Extract data using multiple strategies
            flow_data = await self._extract_flow_data(symbol)

            if not flow_data:
                logger.warning(f"No flow data extracted for {symbol}, trying alternatives")
                flow_data = await self._extract_from_scripts(symbol)

            if not flow_data:
                logger.error(f"Failed to extract flow data for {symbol}")
                await self.browser.take_screenshot(f"ticker_flow_{symbol}_failed")
                return None

            # Update with metadata
            flow_data.source_url = url
            flow_data.is_authenticated = is_authenticated

            self.browser.status.record_success()
            logger.info(
                f"Ticker flow scraped: {symbol}, "
                f"net_premium=${flow_data.net_premium:,.0f}, "
                f"sentiment={flow_data.sentiment_score:.2f}"
            )

            return flow_data

        except Exception as e:
            logger.error(f"Error scraping ticker flow for {symbol}: {e}")
            self.browser.status.record_failure(
                ScraperStatusCode.PARSE_ERROR,
                str(e)
            )
            await self.browser.take_screenshot(f"ticker_flow_{symbol}_error")
            return None

    async def _extract_flow_data(self, symbol: str) -> Optional[TickerFlowData]:
        """
        Extract flow data from DOM elements.

        Tries multiple selector strategies.
        """
        page = await self.browser.get_page()

        # Strategy 1: Look for summary/stat cards
        try:
            data = await self._extract_from_summary(page, symbol)
            if data:
                logger.debug(f"Extracted {symbol} data from summary cards")
                return data
        except Exception as e:
            logger.debug(f"Summary extraction failed for {symbol}: {e}")

        # Strategy 2: Look for chart legend/values
        try:
            data = await self._extract_from_chart(page, symbol)
            if data:
                logger.debug(f"Extracted {symbol} data from chart")
                return data
        except Exception as e:
            logger.debug(f"Chart extraction failed for {symbol}: {e}")

        # Strategy 3: Look for text patterns in the page
        try:
            data = await self._extract_from_text(page, symbol)
            if data:
                logger.debug(f"Extracted {symbol} data from text patterns")
                return data
        except Exception as e:
            logger.debug(f"Text extraction failed for {symbol}: {e}")

        return None

    async def _extract_from_summary(self, page, symbol: str) -> Optional[TickerFlowData]:
        """Extract from summary/stat cards on the page"""

        call_premium = 0.0
        put_premium = 0.0
        call_volume = 0
        put_volume = 0

        # Look for stat cards or summary elements
        selectors = [
            '[class*="stat"]',
            '[class*="card"]',
            '[class*="summary"]',
            '[class*="metric"]',
            '[class*="value"]',
        ]

        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    text_lower = text.lower()

                    # Parse call data
                    if 'call' in text_lower:
                        if 'premium' in text_lower or '$' in text:
                            value = self._parse_dollar_value(text)
                            if value is not None and value > call_premium:
                                call_premium = value
                        if 'volume' in text_lower or 'vol' in text_lower:
                            value = self._parse_number(text)
                            if value is not None and value > call_volume:
                                call_volume = int(value)

                    # Parse put data
                    elif 'put' in text_lower:
                        if 'premium' in text_lower or '$' in text:
                            value = self._parse_dollar_value(text)
                            if value is not None and value > put_premium:
                                put_premium = value
                        if 'volume' in text_lower or 'vol' in text_lower:
                            value = self._parse_number(text)
                            if value is not None and value > put_volume:
                                put_volume = int(value)

                    # Parse net premium directly
                    elif 'net' in text_lower and ('premium' in text_lower or '$' in text):
                        value = self._parse_dollar_value(text)
                        if value is not None:
                            # If net is positive, assign to calls, else to puts
                            if value > 0:
                                call_premium = abs(value)
                            else:
                                put_premium = abs(value)

            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")

        if call_premium > 0 or put_premium > 0 or call_volume > 0 or put_volume > 0:
            return TickerFlowData(
                symbol=symbol,
                timestamp=datetime.now(),
                net_premium=call_premium - put_premium,
                call_premium=call_premium,
                put_premium=put_premium,
                call_volume=call_volume,
                put_volume=put_volume,
            )

        return None

    async def _extract_from_chart(self, page, symbol: str) -> Optional[TickerFlowData]:
        """Extract data from chart elements (legends, tooltips, labels)"""

        call_premium = 0.0
        put_premium = 0.0
        call_volume = 0
        put_volume = 0

        # Look for chart legends and labels
        try:
            # Many charts have legend items
            legend_items = await page.query_selector_all(
                '[class*="legend"], [class*="label"], svg text, [class*="recharts"]'
            )

            for item in legend_items:
                text = await item.inner_text() if hasattr(item, 'inner_text') else ''
                if not text:
                    text = await item.get_attribute('textContent') or ''

                text_lower = text.lower()

                if 'call' in text_lower:
                    value = self._parse_dollar_value(text) or self._parse_number(text)
                    if value:
                        if '$' in text or 'premium' in text_lower:
                            call_premium = float(value)
                        else:
                            call_volume = int(value)

                elif 'put' in text_lower:
                    value = self._parse_dollar_value(text) or self._parse_number(text)
                    if value:
                        if '$' in text or 'premium' in text_lower:
                            put_premium = float(value)
                        else:
                            put_volume = int(value)

        except Exception as e:
            logger.debug(f"Chart legend extraction error: {e}")

        # Try to get data from chart tooltip by hovering
        try:
            chart = await page.query_selector('[class*="chart"], svg')
            if chart:
                # Get chart bounding box and hover in the center
                box = await chart.bounding_box()
                if box:
                    await page.mouse.move(
                        box['x'] + box['width'] / 2,
                        box['y'] + box['height'] / 2
                    )
                    await page.wait_for_timeout(500)

                    # Look for tooltip
                    tooltip = await page.query_selector(
                        '[class*="tooltip"], [role="tooltip"]'
                    )
                    if tooltip:
                        tooltip_text = await tooltip.inner_text()
                        # Parse tooltip for values
                        parsed = self._parse_tooltip(tooltip_text)
                        if parsed:
                            call_premium = parsed.get('call_premium', call_premium)
                            put_premium = parsed.get('put_premium', put_premium)
                            call_volume = parsed.get('call_volume', call_volume)
                            put_volume = parsed.get('put_volume', put_volume)

        except Exception as e:
            logger.debug(f"Chart tooltip extraction error: {e}")

        if call_premium > 0 or put_premium > 0:
            return TickerFlowData(
                symbol=symbol,
                timestamp=datetime.now(),
                net_premium=call_premium - put_premium,
                call_premium=call_premium,
                put_premium=put_premium,
                call_volume=call_volume,
                put_volume=put_volume,
            )

        return None

    async def _extract_from_text(self, page, symbol: str) -> Optional[TickerFlowData]:
        """Extract data using regex patterns on page content"""

        content = await page.content()

        patterns = {
            'call_premium': [
                rf'{symbol}.*?call[s]?\s*premium[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
                r'call[s]?\s*premium[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
                r'call[s]?[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)\s*(?:premium|total)',
            ],
            'put_premium': [
                rf'{symbol}.*?put[s]?\s*premium[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
                r'put[s]?\s*premium[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
                r'put[s]?[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)\s*(?:premium|total)',
            ],
            'call_volume': [
                r'call[s]?\s*vol(?:ume)?[:\s]*([\d,]+)',
            ],
            'put_volume': [
                r'put[s]?\s*vol(?:ume)?[:\s]*([\d,]+)',
            ],
        }

        call_premium = 0.0
        put_premium = 0.0
        call_volume = 0
        put_volume = 0

        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = self._parse_value_string(match.group(1))
                    if value is not None:
                        if key == 'call_premium':
                            call_premium = value
                        elif key == 'put_premium':
                            put_premium = value
                        elif key == 'call_volume':
                            call_volume = int(value)
                        elif key == 'put_volume':
                            put_volume = int(value)
                        break

        if call_premium > 0 or put_premium > 0:
            return TickerFlowData(
                symbol=symbol,
                timestamp=datetime.now(),
                net_premium=call_premium - put_premium,
                call_premium=call_premium,
                put_premium=put_premium,
                call_volume=call_volume,
                put_volume=put_volume,
            )

        return None

    async def _extract_from_scripts(self, symbol: str) -> Optional[TickerFlowData]:
        """Extract data from embedded JavaScript/JSON"""
        page = await self.browser.get_page()

        # Try __NEXT_DATA__
        try:
            next_data = await page.evaluate('''
                () => {
                    const script = document.getElementById('__NEXT_DATA__');
                    if (script) {
                        return JSON.parse(script.textContent);
                    }
                    return null;
                }
            ''')

            if next_data:
                data = self._parse_next_data(next_data, symbol)
                if data:
                    return data

        except Exception as e:
            logger.debug(f"Failed to extract __NEXT_DATA__ for {symbol}: {e}")

        # Try window.__data or similar
        try:
            window_data = await page.evaluate('''
                () => {
                    return window.__data || window.__INITIAL_STATE__ || window.__PRELOADED_STATE__ || null;
                }
            ''')

            if window_data:
                data = self._parse_window_data(window_data, symbol)
                if data:
                    return data

        except Exception as e:
            logger.debug(f"Failed to extract window data for {symbol}: {e}")

        return None

    def _parse_next_data(self, data: Dict[str, Any], symbol: str) -> Optional[TickerFlowData]:
        """Parse Next.js data for ticker flow information"""
        props = data.get('props', {})
        page_props = props.get('pageProps', {})

        # Look for flow data
        flow_data = (
            page_props.get('flowData') or
            page_props.get('tickerFlow') or
            page_props.get('data', {}).get('flow') or
            page_props.get('ticker', {}).get('flow')
        )

        if flow_data:
            return self._parse_flow_dict(flow_data, symbol)

        return None

    def _parse_window_data(self, data: Any, symbol: str) -> Optional[TickerFlowData]:
        """Parse window-level data for ticker flow"""
        if isinstance(data, dict):
            # Look for ticker-specific data
            ticker_data = data.get(symbol) or data.get(symbol.lower())
            if ticker_data:
                return self._parse_flow_dict(ticker_data, symbol)

            # Look for generic flow data
            flow_data = data.get('flow') or data.get('tickerFlow')
            if flow_data:
                return self._parse_flow_dict(flow_data, symbol)

        return None

    def _parse_flow_dict(self, data: Dict[str, Any], symbol: str) -> Optional[TickerFlowData]:
        """Parse a flow data dictionary into TickerFlowData"""
        if not isinstance(data, dict):
            return None

        call_premium = float(
            data.get('callPremium') or
            data.get('call_premium') or
            data.get('netCallPremium') or
            0
        )

        put_premium = float(
            data.get('putPremium') or
            data.get('put_premium') or
            data.get('netPutPremium') or
            0
        )

        call_volume = int(
            data.get('callVolume') or
            data.get('call_volume') or
            0
        )

        put_volume = int(
            data.get('putVolume') or
            data.get('put_volume') or
            0
        )

        net_premium = float(
            data.get('netPremium') or
            data.get('net_premium') or
            (call_premium - put_premium)
        )

        if call_premium or put_premium or net_premium:
            return TickerFlowData(
                symbol=symbol,
                timestamp=datetime.now(),
                net_premium=net_premium,
                call_premium=call_premium,
                put_premium=put_premium,
                call_volume=call_volume,
                put_volume=put_volume,
            )

        return None

    def _parse_tooltip(self, text: str) -> Dict[str, float]:
        """Parse tooltip text for flow values"""
        result = {}

        # Look for call/put values
        call_match = re.search(r'call[s]?[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)', text, re.IGNORECASE)
        if call_match:
            value = self._parse_value_string(call_match.group(1))
            if value:
                result['call_premium'] = value

        put_match = re.search(r'put[s]?[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)', text, re.IGNORECASE)
        if put_match:
            value = self._parse_value_string(put_match.group(1))
            if value:
                result['put_premium'] = value

        return result

    def _parse_dollar_value(self, text: str) -> Optional[float]:
        """Parse a dollar value from text"""
        text = text.replace('$', '').replace(',', '').strip()
        match = re.search(r'([\d.]+)\s*([KMB])?', text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            suffix = (match.group(2) or '').upper()
            multiplier = {'K': 1000, 'M': 1000000, 'B': 1000000000}.get(suffix, 1)
            return value * multiplier
        return None

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse a number from text"""
        text = text.replace(',', '').strip()
        match = re.search(r'([\-\d.]+)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def _parse_value_string(self, text: str) -> Optional[float]:
        """Parse a value string with potential suffixes"""
        text = text.replace('$', '').replace(',', '').strip()
        match = re.search(r'([\-\d.]+)\s*([KMB])?', text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                suffix = (match.group(2) or '').upper()
                multiplier = {'K': 1000, 'M': 1000000, 'B': 1000000000}.get(suffix, 1)
                return value * multiplier
            except ValueError:
                pass
        return None
