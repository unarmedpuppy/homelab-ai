"""
SEC Filings Sentiment Provider
===============================

Integration with SEC EDGAR for sentiment analysis of company filings.
Analyzes 10-K, 10-Q, 8-K, and other filings for sentiment indicators.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    from sec_edgar_downloader import Downloader
except ImportError:
    Downloader = None

try:
    import requests
except ImportError:
    requests = None

# Retry logic with exponential backoff
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        RetryError
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    retry = lambda **kwargs: lambda f: f  # No-op decorator
    stop_after_attempt = None
    wait_exponential = None
    retry_if_exception_type = None
    RetryError = Exception

from ...config.settings import settings
from .models import SymbolSentiment, SentimentLevel, Tweet, TweetSentiment
from .sentiment_analyzer import SentimentAnalyzer
from .repository import SentimentRepository
from ...utils.cache import get_cache_manager
from ...utils.rate_limiter import get_rate_limiter
from ...utils.monitoring import get_usage_monitor

logger = logging.getLogger(__name__)


@dataclass
class SECFiling:
    """SEC filing data model"""
    cik: str
    company_name: str
    filing_type: str  # 10-K, 10-Q, 8-K, etc.
    filing_date: datetime
    accession_number: str
    filing_url: str
    text_content: Optional[str] = None
    sections: Dict[str, str] = None  # Section headers -> content
    
    def __post_init__(self):
        if self.sections is None:
            self.sections = {}


class SECFilingsClient:
    """
    SEC EDGAR API client
    
    Uses sec-edgar-downloader library to fetch and parse SEC filings.
    """
    
    def __init__(self):
        """Initialize SEC EDGAR client"""
        if Downloader is None:
            raise ImportError(
                "sec-edgar-downloader is required for SEC filings integration. "
                "Install with: pip install sec-edgar-downloader"
            )
        
        if requests is None:
            raise ImportError(
                "requests is required for SEC filings integration. "
                "Install with: pip install requests"
            )
        
        self.config = settings.sec_filings
        self.downloader = None
        
        # Initialize downloader with user agent (required by SEC)
        try:
            self.downloader = Downloader(
                company_name=self.config.user_agent,
                email_address=self.config.email_address
            )
            logger.info("SECFilingsClient initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SEC EDGAR downloader: {e}")
            raise
        
        # Cache for ticker to CIK mapping
        self.ticker_to_cik_cache: Dict[str, str] = {}
        # Note: Rate limiting is handled at the provider level using get_rate_limiter()
    
    def is_available(self) -> bool:
        """Check if SEC client is available"""
        return self.downloader is not None
    
    def get_cik_for_ticker(self, ticker: str) -> Optional[str]:
        """
        Get CIK (Central Index Key) for a ticker symbol
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            CIK string or None
        """
        ticker = ticker.upper()
        
        # Check cache
        if ticker in self.ticker_to_cik_cache:
            return self.ticker_to_cik_cache[ticker]
        
        # Note: Rate limiting handled at provider level
        
        if requests is None:
            logger.error("requests library not available for CIK lookup")
            return None
        
        def _fetch_cik():
            """Internal function to fetch CIK with retry logic"""
            # Use SEC EDGAR tickers.json for reliable CIK lookup
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            
            response = requests.get(
                tickers_url,
                headers={"User-Agent": self.config.user_agent},
                timeout=10
            )
            response.raise_for_status()
            
            tickers_data = response.json()
            for entry in tickers_data.values():
                if entry.get("ticker", "").upper() == ticker:
                    cik = str(entry.get("cik_str", ""))
                    if cik:
                        # Pad CIK to 10 digits
                        cik = cik.zfill(10)
                        self.ticker_to_cik_cache[ticker] = cik
                        logger.debug(f"Found CIK {cik} for ticker {ticker}")
                        return cik
            
            logger.warning(f"Could not find CIK for ticker {ticker}")
            return None
        
        try:
            # Apply retry logic if tenacity is available
            if TENACITY_AVAILABLE:
                @retry(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1.0, min=1, max=10),
                    retry=retry_if_exception_type((
                        requests.exceptions.RequestException,
                        requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError,
                        ConnectionError,
                        TimeoutError
                    )),
                    reraise=True
                )
                def _fetch_with_retry():
                    return _fetch_cik()
                
                try:
                    return _fetch_with_retry()
                except RetryError as e:
                    logger.error(f"Failed to fetch CIK for {ticker} after retries: {e}")
                    return None
                except (requests.exceptions.RequestException, TimeoutError, ConnectionError) as e:
                    logger.error(f"Error getting CIK for {ticker}: {e}")
                    return None
            else:
                # No retry library, just try once
                try:
                    return _fetch_cik()
                except Exception as e:
                    logger.error(f"Error getting CIK for {ticker}: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"Unexpected error getting CIK for {ticker}: {e}", exc_info=True)
            return None
    
    def get_recent_filings(
        self,
        ticker: str,
        filing_types: List[str] = None,
        limit: int = 5
    ) -> List[SECFiling]:
        """
        Get recent SEC filings for a ticker
        
        Args:
            ticker: Stock ticker symbol
            filing_types: List of filing types to fetch (e.g., ["10-K", "10-Q", "8-K"])
            limit: Maximum number of filings per type
            
        Returns:
            List of SECFiling objects
        """
        if not self.is_available():
            logger.warning("SEC client not available")
            return []
        
        if filing_types is None:
            filing_types = ["10-K", "10-Q", "8-K"]
        
        # Get CIK for ticker
        cik = self.get_cik_for_ticker(ticker)
        if not cik:
            logger.warning(f"Could not find CIK for ticker {ticker}")
            return []
        
        filings = []
        
        for filing_type in filing_types:
            try:
                # Note: Rate limiting handled at provider level
                
                # Download filings using sec-edgar-downloader
                # Note: This downloads to disk, we'll read the content
                filings_list = self.downloader.get_all_available_filings(
                    ticker=ticker,
                    filing_type=filing_type,
                    limit=limit
                )
                
                # Parse filings
                for filing_path, filing_date, accession_number in filings_list[:limit]:
                    try:
                        filing = self._parse_filing(
                            cik=cik,
                            ticker=ticker,
                            filing_type=filing_type,
                            filing_date=filing_date,
                            filing_path=filing_path,
                            accession_number=accession_number
                        )
                        
                        if filing:
                            filings.append(filing)
                            
                    except Exception as e:
                        logger.warning(f"Error parsing filing {filing_path}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error fetching {filing_type} filings for {ticker}: {e}")
                continue
        
        logger.info(f"Retrieved {len(filings)} filings for {ticker}")
        return filings
    
    def _parse_filing(
        self,
        cik: str,
        ticker: str,
        filing_type: str,
        filing_date: datetime,
        filing_path: str,
        accession_number: str
    ) -> Optional[SECFiling]:
        """
        Parse a downloaded SEC filing
        
        Args:
            cik: Company CIK
            ticker: Stock ticker
            filing_type: Type of filing
            filing_date: Filing date
            filing_path: Path to downloaded filing
            accession_number: SEC accession number
            
        Returns:
            SECFiling object or None
        """
        try:
            # Read filing content
            with open(filing_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract sections based on filing type
            sections = {}
            text_content = content
            
            if filing_type in ["10-K", "10-Q"]:
                # Extract key sections
                sections = self._extract_10k_sections(content)
            elif filing_type == "8-K":
                # Extract items from 8-K
                sections = self._extract_8k_items(content)
            
            # Get company name from filing
            company_name = self._extract_company_name(content) or ticker
            
            filing = SECFiling(
                cik=cik,
                company_name=company_name,
                filing_type=filing_type,
                filing_date=filing_date,
                accession_number=accession_number,
                filing_url=f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession_number}",
                text_content=text_content,
                sections=sections
            )
            
            return filing
            
        except Exception as e:
            logger.error(f"Error parsing filing: {e}")
            return None
    
    def _extract_10k_sections(self, content: str) -> Dict[str, str]:
        """Extract key sections from 10-K filing"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            "item1": r"(?i)item\s*1[.\s]+.*?business(?=item\s*1a|item\s*2|$)",
            "item1a": r"(?i)item\s*1a[.\s]+.*?risk\s*factors(?=item\s*2|$)",
            "item2": r"(?i)item\s*2[.\s]+.*?properties(?=item\s*3|$)",
            "item7": r"(?i)item\s*7[.\s]+.*?management.*?discussion(?=item\s*8|$)",
            "item7a": r"(?i)item\s*7a[.\s]+.*?quantitative.*?qualitative(?=item\s*8|$)",
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(0)[:5000]  # Limit section size
        
        return sections
    
    def _extract_8k_items(self, content: str) -> Dict[str, str]:
        """Extract items from 8-K filing"""
        sections = {}
        
        # 8-K items
        item_patterns = {
            "item1.01": r"(?i)item\s*1\.01\s+entry\s+into\s+material\s+definitive\s+agreement",
            "item1.02": r"(?i)item\s*1\.02\s+termination\s+of\s+material\s+definitive\s+agreement",
            "item2.01": r"(?i)item\s*2\.01\s+completion\s+of\s+acquisition",
            "item2.02": r"(?i)item\s*2\.02\s+results\s+of\s+operations",
            "item4.01": r"(?i)item\s*4\.01\s+changes\s+in\s+registrant.*?certifying\s+accountant",
            "item8.01": r"(?i)item\s*8\.01\s+other\s+events",
        }
        
        for item_name, pattern in item_patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                # Extract text after the item header
                item_content = match.group(0)
                sections[item_name] = item_content[:3000]  # Limit item size
        
        return sections
    
    def _extract_company_name(self, content: str) -> Optional[str]:
        """Extract company name from filing"""
        # Look for company name patterns
        patterns = [
            r"(?i)company\s+name[:\s]+([A-Z][A-Za-z\s&,\.]+)",
            r"(?i)registrant[:\s]+([A-Z][A-Za-z\s&,\.]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content[:5000])  # Search first 5000 chars
            if match:
                company_name = match.group(1).strip()
                # Clean up
                company_name = re.sub(r'\s+', ' ', company_name)
                if len(company_name) > 5 and len(company_name) < 100:
                    return company_name
        
        return None


class SECFilingsSentimentProvider:
    """
    SEC filings sentiment provider
    
    Analyzes SEC filings (10-K, 10-Q, 8-K) for sentiment indicators.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize SEC filings sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.client = None
        self.analyzer = SentimentAnalyzer()
        self.cache = get_cache_manager()
        self.cache_ttl = settings.sec_filings.cache_ttl if hasattr(settings, 'sec_filings') else 3600
        self.rate_limiter = get_rate_limiter("sec_filings")
        self.usage_monitor = get_usage_monitor()
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        # Initialize client if available
        try:
            self.client = SECFilingsClient()
            logger.info(f"SECFilingsSentimentProvider initialized (persist_to_db={persist_to_db})")
        except ImportError as e:
            logger.warning(f"SEC EDGAR library not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize SEC client: {e}")
    
    def is_available(self) -> bool:
        """Check if SEC provider is available"""
        return self.client is not None and self.client.is_available()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache using Redis-backed cache manager"""
        cache_key = f"sec_filings:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: Any):
        """Store data in cache using Redis-backed cache manager"""
        cache_key = f"sec_filings:{key}"
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
    
    def get_sentiment(
        self,
        symbol: str,
        hours: int = 24,
        filing_types: List[str] = None
    ) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol from recent SEC filings
        
        Args:
            symbol: Stock symbol
            hours: Hours of historical filings to analyze (default: 24)
                   Note: SEC filings are typically quarterly/yearly, so this is converted to days
            filing_types: Types of filings to analyze (default: ["10-K", "10-Q", "8-K"])
            
        Returns:
            SymbolSentiment object or None
        """
        if not self.is_available():
            logger.warning("SEC filings provider not available")
            return None
        
        if filing_types is None:
            filing_types = ["10-K", "10-Q", "8-K"]
        
        # Convert hours to days for SEC filings (since filings are infrequent)
        # For hours < 720 (30 days), search last 30 days minimum
        # For hours >= 720, search proportional days
        days = max(30, int(hours / 24))
        
        # Check rate limit (SEC allows 10 requests per second, but we're conservative)
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=10, window_seconds=1)
        if not is_allowed:
            logger.warning(f"SEC filings rate limit exceeded for {symbol}, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(limit=10, window_seconds=1)
            if rate_status.is_limited:
                logger.error(f"SEC filings rate limit still exceeded after wait")
                self.usage_monitor.record_request("sec_filings", success=False)
                return None
        
        # Check cache
        cache_key = f"sentiment_{symbol}_{hours}_{'_'.join(filing_types)}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached SEC sentiment for {symbol}")
            self.usage_monitor.record_request("sec_filings", success=True, cached=True)
            return cached
        
        try:
            # Fetch recent filings
            filings = self.client.get_recent_filings(
                ticker=symbol,
                filing_types=filing_types,
                limit=3  # Limit per filing type
            )
            
            if not filings:
                logger.info(f"No SEC filings found for {symbol}")
                self.usage_monitor.record_request("sec_filings", success=True)
                return None
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_filings = [f for f in filings if f.filing_date >= cutoff_date]
            
            if not recent_filings:
                logger.info(f"No recent SEC filings for {symbol} in last {days} days (within {hours} hours window)")
                self.usage_monitor.record_request("sec_filings", success=True)
                return None
        except Exception as e:
            logger.error(f"Error fetching SEC filings for {symbol}: {e}", exc_info=True)
            self.usage_monitor.record_request("sec_filings", success=False)
            return None
        
        # Analyze sentiment for each filing
        filing_sentiments = []
        
        for filing in recent_filings:
            # Analyze filing text
            text_to_analyze = filing.text_content or ""
            
            # Prefer key sections for 10-K/10-Q
            if filing.filing_type in ["10-K", "10-Q"] and filing.sections:
                # Combine key sections
                key_sections = [
                    filing.sections.get("item7", ""),  # MD&A
                    filing.sections.get("item1a", ""),  # Risk factors
                ]
                text_to_analyze = "\n\n".join([s for s in key_sections if s])
            
            if not text_to_analyze or len(text_to_analyze) < 100:
                continue
            
            # Convert filing to Tweet-like object for analyzer
            filing_tweet = Tweet(
                tweet_id=f"sec_{filing.accession_number}",
                text=text_to_analyze[:10000],  # Limit text length
                author_id=filing.cik,
                author_username=filing.company_name,
                created_at=filing.filing_date,
                like_count=0,
                retweet_count=0,
                reply_count=0,
                quote_count=0,
                is_retweet=False,
                is_quote=False,
                is_reply=False,
                language="en",
                symbols_mentioned=[symbol.upper()],
                raw_data={"filing_type": filing.filing_type}
            )
            
            # Save to database if persistence enabled
            tweet_model = None
            if self.persist_to_db and self.repository:
                try:
                    tweet_model = self.repository.save_tweet(filing_tweet)
                except Exception as e:
                    logger.warning(f"Failed to save SEC filing to database: {e}")
            
            # Calculate engagement weight (SEC filings have high weight)
            engagement_score = 10.0  # High weight for official filings
            engagement_weight = self.analyzer.calculate_engagement_weight(engagement_score)
            
            # Analyze sentiment
            sentiment_result = self.analyzer.analyze_tweet(
                tweet=filing_tweet,
                symbol=symbol,
                engagement_weight=engagement_weight,
                influencer_weight=1.0
            )
            
            # Save sentiment to database
            if self.persist_to_db and self.repository and tweet_model:
                try:
                    self.repository.save_tweet_sentiment(sentiment_result, tweet_model)
                except Exception as e:
                    logger.warning(f"Failed to save SEC filing sentiment to database: {e}")
            
            filing_sentiments.append(sentiment_result)
        
        if not filing_sentiments:
            return None
        
        # Aggregate sentiment
        mention_count = len(filing_sentiments)
        average_sentiment = sum(fs.sentiment_score for fs in filing_sentiments) / mention_count
        
        # Weighted average (by engagement)
        total_weighted = sum(fs.weighted_score for fs in filing_sentiments)
        total_weight = sum(fs.engagement_score for fs in filing_sentiments)
        
        if total_weight > 0:
            weighted_sentiment = total_weighted / total_weight
        else:
            weighted_sentiment = average_sentiment
        
        # Determine sentiment level
        sentiment_level = self.analyzer._score_to_level(weighted_sentiment)
        
        # Calculate confidence (SEC filings have high confidence)
        avg_confidence = sum(fs.confidence for fs in filing_sentiments) / mention_count
        confidence = min(avg_confidence * 1.2, 1.0)  # Boost confidence for official filings
        
        sentiment = SymbolSentiment(
            symbol=symbol,
            timestamp=datetime.now(),
            mention_count=mention_count,
            average_sentiment=average_sentiment,
            weighted_sentiment=weighted_sentiment,
            influencer_sentiment=None,
            engagement_score=sum(fs.engagement_score for fs in filing_sentiments) / mention_count,
            sentiment_level=sentiment_level,
            confidence=confidence,
            volume_trend="stable",
            tweets=filing_sentiments[:5]  # Store top 5 filings
        )
        
        # Save symbol sentiment to database
        if self.persist_to_db and self.repository:
            try:
                self.repository.save_symbol_sentiment(sentiment)
            except Exception as e:
                logger.warning(f"Failed to save SEC symbol sentiment to database: {e}")
        
        # Cache result
        self._set_cache(cache_key, sentiment)
        
        logger.info(
            f"SEC filings sentiment for {symbol}: {weighted_sentiment:.3f} "
            f"({sentiment_level.value}) - {mention_count} filings"
        )
        
        # Record successful request
        self.usage_monitor.record_request("sec_filings", success=True)
        
        return sentiment

