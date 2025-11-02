"""
Sentiment Data Models
=====================

Data models for sentiment analysis and aggregation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SentimentLevel(Enum):
    """Sentiment level enumeration"""
    VERY_BEARISH = "very_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    VERY_BULLISH = "very_bullish"


@dataclass
class Tweet:
    """Twitter tweet data model"""
    tweet_id: str
    text: str
    author_id: str
    author_username: str
    created_at: datetime
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    is_retweet: bool = False
    is_quote: bool = False
    is_reply: bool = False
    language: Optional[str] = None
    symbols_mentioned: List[str] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class TweetSentiment:
    """Sentiment analysis result for a tweet"""
    tweet_id: str
    symbol: str
    sentiment_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    sentiment_level: SentimentLevel
    vader_scores: Dict[str, float] = field(default_factory=dict)
    engagement_score: float = 0.0
    influencer_weight: float = 1.0
    weighted_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SymbolSentiment:
    """Aggregated sentiment for a symbol"""
    symbol: str
    timestamp: datetime
    mention_count: int
    average_sentiment: float  # -1.0 to 1.0
    weighted_sentiment: float  # -1.0 to 1.0
    influencer_sentiment: Optional[float] = None
    engagement_score: float = 0.0
    sentiment_level: SentimentLevel = SentimentLevel.NEUTRAL
    confidence: float = 0.0
    volume_trend: str = "stable"  # up, down, stable
    tweets: List[TweetSentiment] = field(default_factory=list)


@dataclass
class Influencer:
    """Twitter influencer/trader account"""
    user_id: str
    username: str
    display_name: str
    follower_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    is_verified: bool = False
    is_protected: bool = False
    category: str = "unknown"  # trader, analyst, news, education, etc.
    weight_multiplier: float = 1.5
    is_active: bool = True
    added_at: datetime = field(default_factory=datetime.now)

