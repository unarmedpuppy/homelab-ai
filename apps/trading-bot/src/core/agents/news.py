"""
News Analyst Agent (T7: Analyst Agents)
========================================

Analyzes news articles and press releases to produce trading recommendations.
Evaluates news sentiment, impact, and relevance.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import (
    AnalystAgent,
    AnalystConfidence,
    AnalystRecommendation,
    AnalystReport,
    SignalStrength,
)

logger = logging.getLogger(__name__)


class NewsAnalyst(AnalystAgent):
    """
    News analysis agent that evaluates news articles and their market impact.

    Analyzes:
    - News sentiment (positive/negative)
    - News recency and relevance
    - Source credibility
    - Event types (earnings, M&A, regulatory, etc.)
    - Volume of news coverage
    """

    def __init__(
        self,
        name: str = "News Analyst",
        recency_hours: int = 24,
        min_articles: int = 1,
    ):
        """
        Initialize News Analyst.

        Args:
            name: Analyst name
            recency_hours: Hours to consider news as recent
            min_articles: Minimum articles needed for analysis
        """
        super().__init__(name=name, analyst_type="news")

        self.recency_hours = recency_hours
        self.min_articles = min_articles
        self._news_provider = None

    @property
    def news_provider(self):
        """Lazy load news sentiment provider"""
        if self._news_provider is None:
            try:
                from ...data.providers.sentiment.news import NewsSentimentProvider
                self._news_provider = NewsSentimentProvider()
            except ImportError:
                logger.warning("NewsSentimentProvider not available")
        return self._news_provider

    async def analyze(
        self,
        symbol: str,
        news_data: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AnalystReport:
        """
        Analyze news for a symbol.

        Args:
            symbol: Trading symbol to analyze
            news_data: Optional list of news articles with sentiment
            **kwargs: Additional parameters

        Returns:
            AnalystReport with news analysis results
        """
        try:
            # Fetch news if not provided
            if news_data is None:
                news_data = await self._fetch_news(symbol)

            if not news_data:
                return self._create_empty_report(symbol, "No news data available")

            # Filter to recent news
            cutoff_time = datetime.now() - timedelta(hours=self.recency_hours)
            recent_news = self._filter_recent_news(news_data, cutoff_time)

            if len(recent_news) < self.min_articles:
                return self._create_empty_report(
                    symbol, f"Insufficient recent news ({len(recent_news)} articles)"
                )

            # Analyze news
            sentiment_analysis = self._analyze_sentiment(recent_news)
            event_analysis = self._analyze_events(recent_news)
            volume_analysis = self._analyze_volume(recent_news, news_data)

            # Combine analyses
            combined = self._combine_analyses(
                sentiment_analysis,
                event_analysis,
                volume_analysis,
            )

            # Build key factors
            key_factors = []
            warnings = []

            if sentiment_analysis["signal"] != "neutral":
                key_factors.append(
                    f"News sentiment: {sentiment_analysis['signal']} "
                    f"({sentiment_analysis['score']:.2f})"
                )

            if sentiment_analysis["article_count"] > 0:
                key_factors.append(f"{sentiment_analysis['article_count']} recent articles analyzed")

            if event_analysis.get("significant_events"):
                for event in event_analysis["significant_events"][:3]:
                    key_factors.append(f"Event: {event['type']}")

            if volume_analysis["signal"] != "normal":
                key_factors.append(f"News volume: {volume_analysis['signal']}")

            # Add warnings
            if sentiment_analysis.get("mixed"):
                warnings.append("Mixed news sentiment - conflicting signals")
            if event_analysis.get("high_impact_pending"):
                warnings.append("High-impact event pending (earnings, etc.)")
            if volume_analysis.get("unusual"):
                warnings.append("Unusual news volume - potential volatility")

            # News has shorter validity
            expires_at = datetime.now() + timedelta(hours=2)

            # Build report
            return AnalystReport(
                analyst_name=self.name,
                analyst_type=self.analyst_type,
                symbol=symbol,
                recommendation=self._score_to_recommendation(combined["score"]),
                confidence=self._score_to_confidence(combined["confidence"]),
                confidence_score=combined["confidence"],
                signal_strength=self._score_to_signal_strength(combined["score"]),
                directional_bias=combined["bias"],
                summary=self._generate_summary(sentiment_analysis, event_analysis, combined),
                key_factors=key_factors,
                warnings=warnings,
                metrics={
                    "sentiment_score": sentiment_analysis["score"],
                    "article_count": sentiment_analysis["article_count"],
                    "positive_count": sentiment_analysis.get("positive_count", 0),
                    "negative_count": sentiment_analysis.get("negative_count", 0),
                    "neutral_count": sentiment_analysis.get("neutral_count", 0),
                    "news_volume_ratio": volume_analysis.get("ratio", 1.0),
                    "event_count": len(event_analysis.get("events", [])),
                },
                raw_data={
                    "sentiment_analysis": sentiment_analysis,
                    "event_analysis": event_analysis,
                    "volume_analysis": volume_analysis,
                    "recent_headlines": [
                        n.get("title", n.get("headline", ""))[:100]
                        for n in recent_news[:5]
                    ],
                },
                expires_at=expires_at,
                data_freshness_seconds=0.0,
            )

        except Exception as e:
            logger.error(f"News analysis error for {symbol}: {e}", exc_info=True)
            return self._create_empty_report(symbol, f"Analysis error: {str(e)}")

    async def _fetch_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch news articles for symbol"""
        if self.news_provider is None:
            return []

        try:
            # Try to get news from provider
            sentiment = await self.news_provider.get_sentiment(symbol)
            if sentiment and hasattr(sentiment, "raw_data"):
                return sentiment.raw_data.get("articles", [])
            return []
        except Exception as e:
            logger.warning(f"Error fetching news for {symbol}: {e}")
            return []

    def _filter_recent_news(
        self, news_data: List[Dict[str, Any]], cutoff: datetime
    ) -> List[Dict[str, Any]]:
        """Filter news to only recent articles"""
        recent = []
        for article in news_data:
            # Try various date field names
            date_str = article.get("published_at") or article.get("date") or article.get("timestamp")
            if date_str:
                try:
                    if isinstance(date_str, str):
                        article_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    elif isinstance(date_str, datetime):
                        article_date = date_str
                    else:
                        continue

                    # Make naive for comparison if needed
                    if article_date.tzinfo is not None:
                        article_date = article_date.replace(tzinfo=None)

                    if article_date >= cutoff:
                        recent.append(article)
                except (ValueError, TypeError):
                    # Include if we can't parse date
                    recent.append(article)
            else:
                # Include if no date
                recent.append(article)

        return recent

    def _analyze_sentiment(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment across news articles"""
        analysis = {
            "score": 0.0,
            "signal": "neutral",
            "article_count": len(news_data),
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "mixed": False,
        }

        if not news_data:
            return analysis

        sentiments = []
        for article in news_data:
            # Get sentiment score from article
            sentiment = article.get("sentiment") or article.get("sentiment_score")
            if sentiment is not None:
                if isinstance(sentiment, (int, float)):
                    sentiments.append(float(sentiment))
                    if sentiment > 0.1:
                        analysis["positive_count"] += 1
                    elif sentiment < -0.1:
                        analysis["negative_count"] += 1
                    else:
                        analysis["neutral_count"] += 1
                elif isinstance(sentiment, str):
                    # Convert text sentiment to score
                    sentiment_map = {
                        "positive": 0.5,
                        "negative": -0.5,
                        "neutral": 0.0,
                        "bullish": 0.5,
                        "bearish": -0.5,
                    }
                    score = sentiment_map.get(sentiment.lower(), 0.0)
                    sentiments.append(score)
                    if score > 0:
                        analysis["positive_count"] += 1
                    elif score < 0:
                        analysis["negative_count"] += 1
                    else:
                        analysis["neutral_count"] += 1

        if sentiments:
            # Average sentiment
            analysis["score"] = sum(sentiments) / len(sentiments)
            analysis["signal"] = self._sentiment_to_signal(analysis["score"])

            # Check for mixed signals
            if analysis["positive_count"] > 0 and analysis["negative_count"] > 0:
                ratio = min(analysis["positive_count"], analysis["negative_count"]) / max(
                    analysis["positive_count"], analysis["negative_count"]
                )
                if ratio > 0.5:  # More than 50% ratio means mixed
                    analysis["mixed"] = True

        return analysis

    def _analyze_events(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze significant events from news"""
        analysis = {
            "events": [],
            "significant_events": [],
            "high_impact_pending": False,
        }

        # Event keywords and their impact
        event_keywords = {
            "earnings": {"type": "earnings", "impact": "high"},
            "revenue": {"type": "earnings", "impact": "high"},
            "profit": {"type": "earnings", "impact": "high"},
            "acquisition": {"type": "m&a", "impact": "high"},
            "merger": {"type": "m&a", "impact": "high"},
            "buyout": {"type": "m&a", "impact": "high"},
            "fda": {"type": "regulatory", "impact": "high"},
            "sec": {"type": "regulatory", "impact": "medium"},
            "lawsuit": {"type": "legal", "impact": "medium"},
            "settlement": {"type": "legal", "impact": "medium"},
            "upgrade": {"type": "analyst", "impact": "medium"},
            "downgrade": {"type": "analyst", "impact": "medium"},
            "dividend": {"type": "dividend", "impact": "low"},
            "buyback": {"type": "buyback", "impact": "low"},
            "guidance": {"type": "guidance", "impact": "high"},
            "forecast": {"type": "guidance", "impact": "medium"},
        }

        for article in news_data:
            title = (article.get("title") or article.get("headline") or "").lower()
            content = (article.get("content") or article.get("summary") or "").lower()
            text = f"{title} {content}"

            for keyword, event_info in event_keywords.items():
                if keyword in text:
                    event = {
                        "type": event_info["type"],
                        "impact": event_info["impact"],
                        "keyword": keyword,
                        "title": article.get("title") or article.get("headline", ""),
                    }
                    analysis["events"].append(event)

                    if event_info["impact"] == "high":
                        analysis["significant_events"].append(event)

        # Check for pending high-impact events
        pending_keywords = ["upcoming", "expected", "scheduled", "will report", "to announce"]
        for article in news_data:
            title = (article.get("title") or article.get("headline") or "").lower()
            if any(kw in title for kw in pending_keywords):
                if any(kw in title for kw in ["earnings", "revenue", "guidance"]):
                    analysis["high_impact_pending"] = True
                    break

        return analysis

    def _analyze_volume(
        self, recent_news: List[Dict[str, Any]], all_news: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze news volume patterns"""
        analysis = {
            "signal": "normal",
            "ratio": 1.0,
            "unusual": False,
        }

        recent_count = len(recent_news)
        total_count = len(all_news)

        if total_count > 0:
            # Expected recent count based on recency window
            expected_ratio = self.recency_hours / 168  # Assume week of news
            expected_count = max(1, total_count * expected_ratio)
            analysis["ratio"] = recent_count / expected_count

            if analysis["ratio"] > 2.0:
                analysis["signal"] = "high"
                analysis["unusual"] = True
            elif analysis["ratio"] > 1.5:
                analysis["signal"] = "elevated"
            elif analysis["ratio"] < 0.5:
                analysis["signal"] = "low"

        return analysis

    def _sentiment_to_signal(self, sentiment: float) -> str:
        """Convert sentiment score to signal string"""
        if sentiment >= 0.4:
            return "very_positive"
        elif sentiment >= 0.15:
            return "positive"
        elif sentiment >= 0.05:
            return "slightly_positive"
        elif sentiment <= -0.4:
            return "very_negative"
        elif sentiment <= -0.15:
            return "negative"
        elif sentiment <= -0.05:
            return "slightly_negative"
        else:
            return "neutral"

    def _combine_analyses(
        self,
        sentiment: Dict[str, Any],
        events: Dict[str, Any],
        volume: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Combine analyses into overall score"""
        # Base score from sentiment
        base_score = sentiment["score"]

        # Adjust for events
        event_modifier = 0.0
        for event in events.get("significant_events", []):
            # Events can amplify the sentiment direction
            if event["impact"] == "high":
                event_modifier += 0.1 * (1 if base_score >= 0 else -1)

        total_score = base_score + event_modifier
        total_score = max(-1.0, min(1.0, total_score))

        # Calculate confidence
        # More articles = higher confidence
        article_count = sentiment["article_count"]
        article_confidence = min(1.0, article_count / 10)  # Max at 10 articles

        # Reduce confidence for mixed signals
        if sentiment.get("mixed"):
            article_confidence *= 0.7

        # Base confidence
        confidence = 0.3 + (article_confidence * 0.5)

        # Boost for significant events
        if events.get("significant_events"):
            confidence = min(1.0, confidence + 0.15)

        return {
            "score": total_score,
            "bias": total_score,
            "confidence": confidence,
        }

    def _generate_summary(
        self,
        sentiment: Dict[str, Any],
        events: Dict[str, Any],
        combined: Dict[str, Any],
    ) -> str:
        """Generate human-readable summary"""
        score = combined["score"]

        if score >= 0.3:
            direction = "strongly positive"
        elif score >= 0.1:
            direction = "positive"
        elif score >= 0.03:
            direction = "slightly positive"
        elif score <= -0.3:
            direction = "strongly negative"
        elif score <= -0.1:
            direction = "negative"
        elif score <= -0.03:
            direction = "slightly negative"
        else:
            direction = "neutral"

        articles = sentiment["article_count"]
        summary = f"News sentiment is {direction} based on {articles} recent articles. "

        if events.get("significant_events"):
            event_types = list(set(e["type"] for e in events["significant_events"]))
            summary += f"Significant events: {', '.join(event_types)}. "

        if sentiment.get("mixed"):
            summary += "Note: Mixed signals in news coverage. "

        summary += f"Confidence: {combined['confidence'] * 100:.0f}%"

        return summary
