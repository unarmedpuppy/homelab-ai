"""
Market Tide Scraper
===================

Scrapes market tide data from the Unusual Whales flow overview page.
Extracts net call/put premium and volume data.

Target URL: https://unusualwhales.com/flow/overview
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from ..browser import UWBrowserSession
from ..models import MarketTideDataPoint, MarketTideSnapshot, ScraperStatusCode
from ..config import get_settings

logger = logging.getLogger(__name__)


class MarketTideScraper:
    """
    Scraper for Unusual Whales Market Tide data.

    Extracts:
    - Net call premium
    - Net put premium
    - Net volume differential
    - Cumulative premium data (if available)
    """

    def __init__(self, browser: UWBrowserSession):
        """
        Initialize the market tide scraper.

        Args:
            browser: Browser session to use for scraping
        """
        self.browser = browser
        self.settings = get_settings()

    async def scrape(self) -> Optional[MarketTideSnapshot]:
        """
        Scrape market tide data from the overview page.

        Returns:
            MarketTideSnapshot with extracted data, or None if failed.
        """
        url = self.settings.market_tide_url
        logger.info(f"Scraping market tide from {url}")

        try:
            # Ensure we're authenticated for full data
            is_authenticated = await self.browser.ensure_authenticated()

            # Navigate to the page
            success = await self.browser.navigate(url)
            if not success:
                logger.error("Failed to navigate to market tide page")
                return None

            # Wait for the page to fully render (React/Next.js app)
            # Look for common chart or data containers
            await self.browser.wait_for_selector(
                '[class*="chart"], [class*="flow"], [class*="tide"], [data-testid]',
                timeout=15000
            )

            # Extract data using multiple strategies
            data_points = await self._extract_data_points()

            if not data_points:
                logger.warning("No data points extracted, trying alternative methods")
                data_points = await self._extract_data_from_scripts()

            if not data_points:
                logger.error("Failed to extract market tide data")
                await self.browser.take_screenshot("market_tide_extraction_failed")
                return None

            snapshot = MarketTideSnapshot(
                data_points=data_points,
                fetch_timestamp=datetime.now(),
                is_authenticated=is_authenticated,
            )

            self.browser.status.record_success()
            logger.info(
                f"Market tide scraped: {len(data_points)} points, "
                f"sentiment={snapshot.overall_sentiment:.2f}"
            )

            return snapshot

        except Exception as e:
            logger.error(f"Error scraping market tide: {e}")
            self.browser.status.record_failure(
                ScraperStatusCode.PARSE_ERROR,
                str(e)
            )
            await self.browser.take_screenshot("market_tide_error")
            return None

    async def _extract_data_points(self) -> List[MarketTideDataPoint]:
        """
        Extract data points from DOM elements.

        This method tries multiple selector strategies since the DOM
        structure may vary.
        """
        data_points = []
        page = await self.browser.get_page()

        # Strategy 1: Look for chart data in SVG/canvas elements
        # Many charting libraries encode data in the DOM
        try:
            # Look for flow/tide summary cards
            summary_data = await self._extract_summary_cards(page)
            if summary_data:
                data_points.append(summary_data)
                logger.debug("Extracted data from summary cards")
        except Exception as e:
            logger.debug(f"Summary card extraction failed: {e}")

        # Strategy 2: Look for table rows with flow data
        try:
            table_data = await self._extract_from_tables(page)
            if table_data:
                data_points.extend(table_data)
                logger.debug(f"Extracted {len(table_data)} points from tables")
        except Exception as e:
            logger.debug(f"Table extraction failed: {e}")

        # Strategy 3: Look for specific text patterns
        try:
            text_data = await self._extract_from_text_patterns(page)
            if text_data:
                data_points.append(text_data)
                logger.debug("Extracted data from text patterns")
        except Exception as e:
            logger.debug(f"Text pattern extraction failed: {e}")

        return data_points

    async def _extract_summary_cards(self, page) -> Optional[MarketTideDataPoint]:
        """Extract data from summary/stat cards typically at the top of the page"""

        # Common patterns for premium/volume displays
        selectors = [
            # Cards with labels
            '[class*="stat"], [class*="card"], [class*="summary"]',
            # Direct value containers
            '[class*="premium"], [class*="volume"], [class*="flow"]',
        ]

        call_premium = 0.0
        put_premium = 0.0
        net_volume = 0

        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    text_lower = text.lower()

                    # Look for call premium
                    if 'call' in text_lower and ('premium' in text_lower or '$' in text):
                        value = self._parse_dollar_value(text)
                        if value is not None:
                            call_premium = value

                    # Look for put premium
                    elif 'put' in text_lower and ('premium' in text_lower or '$' in text):
                        value = self._parse_dollar_value(text)
                        if value is not None:
                            put_premium = value

                    # Look for volume
                    elif 'volume' in text_lower or 'vol' in text_lower:
                        value = self._parse_number(text)
                        if value is not None:
                            # If it contains "net", it's already net volume
                            # Otherwise we'll need to calculate
                            net_volume = int(value)

            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")

        if call_premium > 0 or put_premium > 0 or net_volume != 0:
            return MarketTideDataPoint(
                timestamp=datetime.now(),
                net_call_premium=call_premium,
                net_put_premium=put_premium,
                net_volume=net_volume,
            )

        return None

    async def _extract_from_tables(self, page) -> List[MarketTideDataPoint]:
        """Extract data from table elements"""
        data_points = []

        # Look for tables with flow data
        tables = await page.query_selector_all('table, [role="table"], [class*="table"]')

        for table in tables:
            try:
                rows = await table.query_selector_all('tr, [role="row"]')
                for row in rows:
                    cells = await row.query_selector_all('td, [role="cell"]')
                    if len(cells) >= 3:
                        cell_texts = [await cell.inner_text() for cell in cells]

                        # Try to identify columns by header or content
                        data_point = self._parse_table_row(cell_texts)
                        if data_point:
                            data_points.append(data_point)

            except Exception as e:
                logger.debug(f"Error parsing table: {e}")

        return data_points

    async def _extract_from_text_patterns(self, page) -> Optional[MarketTideDataPoint]:
        """Extract data using regex patterns on page text"""

        content = await page.content()

        # Patterns for different value formats
        patterns = {
            'call_premium': [
                r'call[s]?\s*premium[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
                r'net\s*call[s]?[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
                r'calls[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
            ],
            'put_premium': [
                r'put[s]?\s*premium[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
                r'net\s*put[s]?[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
                r'puts[:\s]*\$?([\d,]+(?:\.\d+)?[KMB]?)',
            ],
            'net_volume': [
                r'net\s*volume[:\s]*([\-\d,]+)',
                r'volume\s*diff[:\s]*([\-\d,]+)',
            ],
        }

        call_premium = 0.0
        put_premium = 0.0
        net_volume = 0

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
                        elif key == 'net_volume':
                            net_volume = int(value)
                        break

        if call_premium > 0 or put_premium > 0:
            return MarketTideDataPoint(
                timestamp=datetime.now(),
                net_call_premium=call_premium,
                net_put_premium=put_premium,
                net_volume=net_volume,
            )

        return None

    async def _extract_data_from_scripts(self) -> List[MarketTideDataPoint]:
        """
        Extract data from JavaScript/JSON embedded in the page.

        Many React apps include initial data in script tags.
        """
        data_points = []
        page = await self.browser.get_page()

        try:
            # Look for __NEXT_DATA__ which Next.js apps use
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
                data_points.extend(self._parse_next_data(next_data))

        except Exception as e:
            logger.debug(f"Failed to extract __NEXT_DATA__: {e}")

        try:
            # Look for any JSON data in script tags
            scripts_data = await page.evaluate('''
                () => {
                    const results = [];
                    const scripts = document.querySelectorAll('script[type="application/json"]');
                    scripts.forEach(script => {
                        try {
                            results.push(JSON.parse(script.textContent));
                        } catch (e) {}
                    });
                    return results;
                }
            ''')

            for script_json in scripts_data or []:
                data_points.extend(self._parse_json_data(script_json))

        except Exception as e:
            logger.debug(f"Failed to extract JSON from scripts: {e}")

        return data_points

    def _parse_next_data(self, data: Dict[str, Any]) -> List[MarketTideDataPoint]:
        """Parse Next.js __NEXT_DATA__ structure for flow data"""
        data_points = []

        # Navigate through common Next.js data structures
        props = data.get('props', {})
        page_props = props.get('pageProps', {})

        # Look for flow/tide data in various possible locations
        flow_data = (
            page_props.get('flowData') or
            page_props.get('tideData') or
            page_props.get('marketData') or
            page_props.get('data', {}).get('flow') or
            page_props.get('initialData', {}).get('flow')
        )

        if isinstance(flow_data, list):
            for item in flow_data:
                data_point = self._parse_flow_item(item)
                if data_point:
                    data_points.append(data_point)

        elif isinstance(flow_data, dict):
            # Could be aggregated data
            data_point = self._parse_flow_item(flow_data)
            if data_point:
                data_points.append(data_point)

        return data_points

    def _parse_json_data(self, data: Any) -> List[MarketTideDataPoint]:
        """Parse generic JSON structure for flow data"""
        data_points = []

        if isinstance(data, dict):
            # Look for common keys
            for key in ['flow', 'tide', 'premium', 'data', 'results']:
                if key in data:
                    sub_data = data[key]
                    if isinstance(sub_data, list):
                        for item in sub_data:
                            dp = self._parse_flow_item(item)
                            if dp:
                                data_points.append(dp)
                    elif isinstance(sub_data, dict):
                        dp = self._parse_flow_item(sub_data)
                        if dp:
                            data_points.append(dp)

        elif isinstance(data, list):
            for item in data:
                dp = self._parse_flow_item(item)
                if dp:
                    data_points.append(dp)

        return data_points

    def _parse_flow_item(self, item: Dict[str, Any]) -> Optional[MarketTideDataPoint]:
        """Parse a single flow data item into a MarketTideDataPoint"""
        if not isinstance(item, dict):
            return None

        # Look for different key variations
        call_premium = (
            item.get('callPremium') or
            item.get('call_premium') or
            item.get('netCallPremium') or
            item.get('net_call_premium') or
            0.0
        )

        put_premium = (
            item.get('putPremium') or
            item.get('put_premium') or
            item.get('netPutPremium') or
            item.get('net_put_premium') or
            0.0
        )

        net_volume = (
            item.get('netVolume') or
            item.get('net_volume') or
            item.get('volumeDiff') or
            item.get('volume_diff') or
            0
        )

        timestamp_raw = (
            item.get('timestamp') or
            item.get('time') or
            item.get('date') or
            item.get('created_at')
        )

        if timestamp_raw:
            try:
                if isinstance(timestamp_raw, (int, float)):
                    # Unix timestamp
                    timestamp = datetime.fromtimestamp(timestamp_raw)
                else:
                    timestamp = datetime.fromisoformat(str(timestamp_raw).replace('Z', '+00:00'))
            except Exception:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        # Only return if we have meaningful data
        if call_premium or put_premium or net_volume:
            return MarketTideDataPoint(
                timestamp=timestamp,
                net_call_premium=float(call_premium),
                net_put_premium=float(put_premium),
                net_volume=int(net_volume),
            )

        return None

    def _parse_table_row(self, cells: List[str]) -> Optional[MarketTideDataPoint]:
        """Parse a table row into a MarketTideDataPoint"""
        call_premium = 0.0
        put_premium = 0.0
        net_volume = 0

        for cell in cells:
            cell_lower = cell.lower()

            # Try to identify what each cell represents
            value = self._parse_value_string(cell)
            if value is None:
                continue

            # Check for indicators in the cell text
            if 'call' in cell_lower:
                call_premium = value
            elif 'put' in cell_lower:
                put_premium = value
            elif 'vol' in cell_lower:
                net_volume = int(value)

        if call_premium or put_premium:
            return MarketTideDataPoint(
                timestamp=datetime.now(),
                net_call_premium=call_premium,
                net_put_premium=put_premium,
                net_volume=net_volume,
            )

        return None

    def _parse_dollar_value(self, text: str) -> Optional[float]:
        """Parse a dollar value from text like '$1.5M' or '$1,500,000'"""
        # Remove common formatting
        text = text.replace('$', '').replace(',', '').strip()

        # Handle K/M/B suffixes
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
