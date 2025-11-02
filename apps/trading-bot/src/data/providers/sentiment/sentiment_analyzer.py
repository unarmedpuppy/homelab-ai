"""
Sentiment Analyzer
==================

VADER-based sentiment analysis for social media text.
"""

import re
import logging
from typing import Dict, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .models import Tweet, TweetSentiment, SentimentLevel

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analyzer using VADER (Valence Aware Dictionary and sEntiment Reasoner)
    
    VADER is optimized for social media text and handles:
    - Emojis and emoticons
    - Slang and abbreviations
    - Punctuation emphasis
    - Negation
    """
    
    def __init__(self):
        """Initialize VADER sentiment analyzer"""
        self.analyzer = SentimentIntensityAnalyzer()
        logger.info("SentimentAnalyzer initialized with VADER")
    
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text using VADER
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores:
            - neg: Negative sentiment (0.0 to 1.0)
            - neu: Neutral sentiment (0.0 to 1.0)
            - pos: Positive sentiment (0.0 to 1.0)
            - compound: Overall sentiment (-1.0 to 1.0)
        """
        # Preprocess text
        processed_text = self._preprocess_text(text)
        
        # Get VADER scores
        scores = self.analyzer.polarity_scores(processed_text)
        
        return {
            'neg': scores['neg'],
            'neu': scores['neu'],
            'pos': scores['pos'],
            'compound': scores['compound']
        }
    
    def analyze_tweet(self, tweet: Tweet, symbol: str, 
                     engagement_weight: float = 1.0,
                     influencer_weight: float = 1.0) -> TweetSentiment:
        """
        Analyze sentiment of a tweet for a specific symbol
        
        Args:
            tweet: Tweet object
            symbol: Stock symbol being analyzed
            engagement_weight: Weight based on engagement (likes/retweets)
            influencer_weight: Weight if from influencer
            
        Returns:
            TweetSentiment object with analyzed sentiment
        """
        # Extract relevant text (mentions of symbol)
        relevant_text = self._extract_relevant_text(tweet.text, symbol)
        
        if not relevant_text:
            # No mention of symbol, return neutral
            return TweetSentiment(
                tweet_id=tweet.tweet_id,
                symbol=symbol,
                sentiment_score=0.0,
                confidence=0.0,
                sentiment_level=SentimentLevel.NEUTRAL
            )
        
        # Analyze sentiment
        vader_scores = self.analyze(relevant_text)
        compound_score = vader_scores['compound']
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(tweet)
        
        # Calculate weighted score
        base_score = compound_score
        weighted_score = base_score * engagement_weight * influencer_weight
        
        # Determine sentiment level
        sentiment_level = self._score_to_level(weighted_score)
        
        # Calculate confidence based on VADER scores
        # Higher confidence when sentiment is more polarized (less neutral)
        confidence = 1.0 - vader_scores['neu']
        
        return TweetSentiment(
            tweet_id=tweet.tweet_id,
            symbol=symbol,
            sentiment_score=compound_score,
            confidence=confidence,
            sentiment_level=sentiment_level,
            vader_scores=vader_scores,
            engagement_score=engagement_score,
            influencer_weight=influencer_weight,
            weighted_score=weighted_score,
            timestamp=tweet.created_at
        )
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for sentiment analysis
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text
        """
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        # Remove stock symbol mentions but keep context
        # Replace $SYMBOL with "stock" to maintain context
        text = re.sub(r'\$[A-Z]{1,5}\b', 'stock', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _extract_relevant_text(self, text: str, symbol: str) -> str:
        """
        Extract text relevant to the symbol being analyzed
        
        Args:
            text: Full tweet text
            symbol: Symbol to search for
            
        Returns:
            Relevant text excerpt or full text if symbol found
        """
        # Check if symbol is mentioned
        pattern = rf'\${symbol}\b|#{symbol}\b|{symbol}\s+(?:stock|shares|equity)'
        
        if re.search(pattern, text, re.IGNORECASE):
            return text
        
        # Return empty if symbol not mentioned
        return ""
    
    def _calculate_engagement_score(self, tweet: Tweet) -> float:
        """
        Calculate engagement score for a tweet
        
        Args:
            tweet: Tweet object
            
        Returns:
            Engagement score (0.0 to 1.0+)
        """
        # Calculate total engagement
        total_engagement = (
            tweet.like_count +
            tweet.retweet_count * 2 +  # Retweets weighted higher
            tweet.reply_count +
            tweet.quote_count * 1.5
        )
        
        # Normalize to 0-1 scale (with potential for >1 for viral tweets)
        # Using logarithmic scaling
        if total_engagement == 0:
            return 0.0
        
        # Log scale: log10(engagement + 1) / log10(10000)
        # This gives 0.0 for 0 engagement, ~1.0 for 10K engagement
        import math
        normalized = math.log10(total_engagement + 1) / math.log10(10000)
        
        return min(normalized, 2.0)  # Cap at 2.0x
    
    def _score_to_level(self, score: float) -> SentimentLevel:
        """
        Convert sentiment score to sentiment level
        
        Args:
            score: Sentiment score (-1.0 to 1.0)
            
        Returns:
            SentimentLevel enum
        """
        if score >= 0.6:
            return SentimentLevel.VERY_BULLISH
        elif score >= 0.2:
            return SentimentLevel.BULLISH
        elif score >= -0.2:
            return SentimentLevel.NEUTRAL
        elif score >= -0.6:
            return SentimentLevel.BEARISH
        else:
            return SentimentLevel.VERY_BEARISH
    
    def calculate_engagement_weight(self, engagement_score: float) -> float:
        """
        Calculate weight multiplier based on engagement
        
        Args:
            engagement_score: Engagement score (0.0 to 2.0)
            
        Returns:
            Weight multiplier (0.5 to 1.5)
        """
        # Map engagement score to weight
        # Low engagement (< 0.2): 0.5x weight
        # Medium engagement (0.2-0.8): 1.0x weight
        # High engagement (> 0.8): 1.5x weight
        
        if engagement_score < 0.2:
            return 0.5
        elif engagement_score < 0.8:
            # Linear interpolation
            return 0.5 + (engagement_score - 0.2) * (0.5 / 0.6)
        else:
            # High engagement
            return 1.0 + min((engagement_score - 0.8) * 0.5, 0.5)

