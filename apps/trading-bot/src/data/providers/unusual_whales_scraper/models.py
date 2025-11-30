"""
Unusual Whales Scraper Data Models
==================================

Data models for the web scraper that extracts market tide and ticker flow data
from Unusual Whales without requiring the paid API subscription.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class ScraperStatusCode(Enum):
    """Status codes for scraper operations"""
    SUCCESS = "success"
    RATE_LIMITED = "rate_limited"
    AUTH_REQUIRED = "auth_required"
    AUTH_FAILED = "auth_failed"
    PARSE_ERROR = "parse_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class MarketTideDataPoint:
    """
    Single timestamp entry for market tide data.

    Represents net call/put premium and volume at a specific point in time.
    """
    timestamp: datetime
    net_call_premium: float  # Total call premium in dollars
    net_put_premium: float   # Total put premium in dollars
    net_volume: int          # Net call/put volume difference (calls - puts)
    cumulative_premium: Optional[float] = None  # Running total if available

    @property
    def net_premium(self) -> float:
        """Net premium (calls - puts)"""
        return self.net_call_premium - self.net_put_premium

    @property
    def premium_ratio(self) -> float:
        """Ratio of call to put premium (>1 = bullish, <1 = bearish)"""
        if self.net_put_premium == 0:
            return float('inf') if self.net_call_premium > 0 else 0.0
        return self.net_call_premium / self.net_put_premium

    @property
    def sentiment_score(self) -> float:
        """
        Normalized sentiment score from -1 (bearish) to 1 (bullish).
        Based on premium ratio.
        """
        ratio = self.premium_ratio
        if ratio == float('inf'):
            return 1.0
        if ratio == 0:
            return -1.0
        # Convert ratio to -1 to 1 scale
        # ratio of 2 = 0.5, ratio of 0.5 = -0.5
        return max(-1.0, min(1.0, (ratio - 1) / (ratio + 1) * 2))


@dataclass
class MarketTideSnapshot:
    """
    Collection of market tide data points with metadata.

    Represents a complete fetch of market tide data from the overview page.
    """
    data_points: List[MarketTideDataPoint]
    fetch_timestamp: datetime
    interval_minutes: int = 5  # Interval between data points
    source_url: str = "https://unusualwhales.com/flow/overview"
    is_authenticated: bool = False

    @property
    def latest(self) -> Optional[MarketTideDataPoint]:
        """Get the most recent data point"""
        if not self.data_points:
            return None
        return max(self.data_points, key=lambda x: x.timestamp)

    @property
    def total_net_premium(self) -> float:
        """Total net premium across all data points"""
        return sum(dp.net_premium for dp in self.data_points)

    @property
    def total_net_volume(self) -> int:
        """Total net volume across all data points"""
        return sum(dp.net_volume for dp in self.data_points)

    @property
    def overall_sentiment(self) -> float:
        """
        Overall sentiment score from -1 (bearish) to 1 (bullish).
        Weighted average of individual data points.
        """
        if not self.data_points:
            return 0.0
        return sum(dp.sentiment_score for dp in self.data_points) / len(self.data_points)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "fetch_timestamp": self.fetch_timestamp.isoformat(),
            "interval_minutes": self.interval_minutes,
            "source_url": self.source_url,
            "is_authenticated": self.is_authenticated,
            "overall_sentiment": self.overall_sentiment,
            "total_net_premium": self.total_net_premium,
            "total_net_volume": self.total_net_volume,
            "data_points": [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "net_call_premium": dp.net_call_premium,
                    "net_put_premium": dp.net_put_premium,
                    "net_volume": dp.net_volume,
                    "cumulative_premium": dp.cumulative_premium,
                    "net_premium": dp.net_premium,
                    "sentiment_score": dp.sentiment_score,
                }
                for dp in self.data_points
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarketTideSnapshot":
        """Create from dictionary (JSON deserialization)"""
        data_points = [
            MarketTideDataPoint(
                timestamp=datetime.fromisoformat(dp["timestamp"]),
                net_call_premium=dp["net_call_premium"],
                net_put_premium=dp["net_put_premium"],
                net_volume=dp["net_volume"],
                cumulative_premium=dp.get("cumulative_premium"),
            )
            for dp in data.get("data_points", [])
        ]
        return cls(
            data_points=data_points,
            fetch_timestamp=datetime.fromisoformat(data["fetch_timestamp"]),
            interval_minutes=data.get("interval_minutes", 5),
            source_url=data.get("source_url", "https://unusualwhales.com/flow/overview"),
            is_authenticated=data.get("is_authenticated", False),
        )


@dataclass
class TickerFlowData:
    """
    Per-ticker options flow data.

    Represents net premium and volume breakdown for a specific symbol.
    """
    symbol: str
    timestamp: datetime
    net_premium: float              # Net premium (calls - puts)
    call_premium: float             # Total call premium
    put_premium: float              # Total put premium
    call_volume: int                # Total call volume
    put_volume: int                 # Total put volume
    net_volume: int = 0             # Net volume (calls - puts)
    premium_ratio: float = 0.0      # Call/put premium ratio
    source_url: str = ""
    is_authenticated: bool = False

    def __post_init__(self):
        """Calculate derived fields"""
        if self.net_volume == 0:
            self.net_volume = self.call_volume - self.put_volume
        if self.premium_ratio == 0.0 and self.put_premium > 0:
            self.premium_ratio = self.call_premium / self.put_premium
        if not self.source_url:
            self.source_url = f"https://unusualwhales.com/option-charts/ticker-flow?ticker_symbol={self.symbol}"

    @property
    def sentiment_score(self) -> float:
        """
        Normalized sentiment score from -1 (bearish) to 1 (bullish).
        Based on premium ratio.
        """
        if self.put_premium == 0:
            return 1.0 if self.call_premium > 0 else 0.0
        ratio = self.call_premium / self.put_premium
        return max(-1.0, min(1.0, (ratio - 1) / (ratio + 1) * 2))

    @property
    def total_volume(self) -> int:
        """Total options volume"""
        return self.call_volume + self.put_volume

    @property
    def total_premium(self) -> float:
        """Total premium (calls + puts)"""
        return self.call_premium + self.put_premium

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "net_premium": self.net_premium,
            "call_premium": self.call_premium,
            "put_premium": self.put_premium,
            "call_volume": self.call_volume,
            "put_volume": self.put_volume,
            "net_volume": self.net_volume,
            "premium_ratio": self.premium_ratio,
            "sentiment_score": self.sentiment_score,
            "total_volume": self.total_volume,
            "total_premium": self.total_premium,
            "source_url": self.source_url,
            "is_authenticated": self.is_authenticated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TickerFlowData":
        """Create from dictionary (JSON deserialization)"""
        return cls(
            symbol=data["symbol"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            net_premium=data["net_premium"],
            call_premium=data["call_premium"],
            put_premium=data["put_premium"],
            call_volume=data["call_volume"],
            put_volume=data["put_volume"],
            net_volume=data.get("net_volume", 0),
            premium_ratio=data.get("premium_ratio", 0.0),
            source_url=data.get("source_url", ""),
            is_authenticated=data.get("is_authenticated", False),
        )


@dataclass
class ScraperStatus:
    """
    Track scraper operation status and health.

    Used for monitoring, debugging, and rate limit management.
    """
    last_fetch_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    last_error_message: Optional[str] = None
    last_status_code: ScraperStatusCode = ScraperStatusCode.SUCCESS
    consecutive_failures: int = 0
    total_fetches: int = 0
    total_successes: int = 0
    total_failures: int = 0
    is_authenticated: bool = False
    session_valid: bool = False

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage"""
        if self.total_fetches == 0:
            return 100.0
        return (self.total_successes / self.total_fetches) * 100

    @property
    def is_healthy(self) -> bool:
        """Check if scraper is in healthy state"""
        return (
            self.consecutive_failures < 3 and
            self.last_status_code == ScraperStatusCode.SUCCESS
        )

    def record_success(self):
        """Record a successful fetch"""
        now = datetime.now()
        self.last_fetch_time = now
        self.last_success_time = now
        self.last_status_code = ScraperStatusCode.SUCCESS
        self.consecutive_failures = 0
        self.total_fetches += 1
        self.total_successes += 1

    def record_failure(self, status_code: ScraperStatusCode, error_message: str):
        """Record a failed fetch"""
        now = datetime.now()
        self.last_fetch_time = now
        self.last_error_time = now
        self.last_error_message = error_message
        self.last_status_code = status_code
        self.consecutive_failures += 1
        self.total_fetches += 1
        self.total_failures += 1

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "last_fetch_time": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "last_error_message": self.last_error_message,
            "last_status_code": self.last_status_code.value,
            "consecutive_failures": self.consecutive_failures,
            "total_fetches": self.total_fetches,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate": self.success_rate,
            "is_healthy": self.is_healthy,
            "is_authenticated": self.is_authenticated,
            "session_valid": self.session_valid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScraperStatus":
        """Create from dictionary (JSON deserialization)"""
        status = cls(
            last_error_message=data.get("last_error_message"),
            last_status_code=ScraperStatusCode(data.get("last_status_code", "success")),
            consecutive_failures=data.get("consecutive_failures", 0),
            total_fetches=data.get("total_fetches", 0),
            total_successes=data.get("total_successes", 0),
            total_failures=data.get("total_failures", 0),
            is_authenticated=data.get("is_authenticated", False),
            session_valid=data.get("session_valid", False),
        )
        if data.get("last_fetch_time"):
            status.last_fetch_time = datetime.fromisoformat(data["last_fetch_time"])
        if data.get("last_success_time"):
            status.last_success_time = datetime.fromisoformat(data["last_success_time"])
        if data.get("last_error_time"):
            status.last_error_time = datetime.fromisoformat(data["last_error_time"])
        return status


@dataclass
class AuthCredentials:
    """
    Authentication credentials for Unusual Whales.

    Used for authenticated scraping with full data access.
    """
    username: str
    password: str
    session_cookie: Optional[str] = None
    cookie_expiry: Optional[datetime] = None

    @property
    def has_valid_session(self) -> bool:
        """Check if session cookie is valid and not expired"""
        if not self.session_cookie:
            return False
        if self.cookie_expiry and datetime.now() > self.cookie_expiry:
            return False
        return True
