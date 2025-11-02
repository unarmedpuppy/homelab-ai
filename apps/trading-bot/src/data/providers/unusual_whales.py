"""
Unusual Whales API Integration
==============================

Integration with Unusual Whales API for options flow data and market sentiment.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class MarketTideLevel(Enum):
    """Market tide levels"""
    VERY_BEARISH = "very_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    VERY_BULLISH = "very_bullish"

class FlowDirection(Enum):
    """Options flow direction"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

@dataclass
class OptionsFlow:
    """Options flow data"""
    symbol: str
    strike: float
    expiry: datetime
    option_type: str  # "call" or "put"
    volume: int
    premium: float
    direction: FlowDirection
    timestamp: datetime
    unusual: bool
    sentiment_score: float  # -1 to 1
    # Enhanced fields
    is_sweep: bool = False
    is_block: bool = False
    pattern_type: Optional[str] = None  # "sweep", "block", "spread", etc.
    sweep_strength: float = 0.0  # 0.0 to 1.0
    open_interest: Optional[int] = None
    implied_volatility: Optional[float] = None

@dataclass
class MarketTide:
    """Market tide data"""
    level: MarketTideLevel
    score: float  # -1 to 1
    timestamp: datetime
    description: str

@dataclass
class UnusualWhalesData:
    """Combined Unusual Whales data"""
    market_tide: MarketTide
    flow_ratio: float  # Bullish flow ratio
    call_premium_delta_ma3: float  # 3-day moving average of call premium delta
    unusual_activity: List[OptionsFlow]
    sentiment_score: float  # Overall sentiment score

class UnusualWhalesClient:
    """Unusual Whales API client"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.unusualwhales.com/api"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = datetime.now().timestamp()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                elif response.status == 429:
                    raise ValueError("Rate limit exceeded")
                else:
                    raise ValueError(f"API request failed with status {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"Network error in Unusual Whales API request: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in Unusual Whales API request: {e}")
            raise
    
    async def get_market_tide(self) -> MarketTide:
        """Get current market tide"""
        try:
            data = await self._make_request("market/tide")
            
            # Parse market tide data
            score = data.get("score", 0.0)
            
            if score >= 0.6:
                level = MarketTideLevel.VERY_BULLISH
            elif score >= 0.2:
                level = MarketTideLevel.BULLISH
            elif score >= -0.2:
                level = MarketTideLevel.NEUTRAL
            elif score >= -0.6:
                level = MarketTideLevel.BEARISH
            else:
                level = MarketTideLevel.VERY_BEARISH
            
            return MarketTide(
                level=level,
                score=score,
                timestamp=datetime.now(),
                description=data.get("description", "")
            )
        except Exception as e:
            logger.error(f"Error getting market tide: {e}")
            # Return neutral tide on error
            return MarketTide(
                level=MarketTideLevel.NEUTRAL,
                score=0.0,
                timestamp=datetime.now(),
                description="Unable to fetch market tide data"
            )
    
    async def get_options_flow(self, symbol: str, hours: int = 24) -> List[OptionsFlow]:
        """Get options flow for a symbol"""
        try:
            params = {
                "symbol": symbol,
                "hours": hours
            }
            
            data = await self._make_request("options/flow", params)
            
            flows = []
            for flow_data in data.get("flows", []):
                # Determine flow direction based on option type and volume
                option_type = flow_data.get("type", "").lower()
                volume = flow_data.get("volume", 0)
                
                if option_type == "call" and volume > 0:
                    direction = FlowDirection.BULLISH
                elif option_type == "put" and volume > 0:
                    direction = FlowDirection.BEARISH
                else:
                    direction = FlowDirection.NEUTRAL
                
                # Calculate sentiment score
                sentiment_score = self._calculate_sentiment_score(flow_data)
                
                flows.append(OptionsFlow(
                    symbol=symbol,
                    strike=flow_data.get("strike", 0.0),
                    expiry=datetime.fromisoformat(flow_data.get("expiry", "")),
                    option_type=option_type,
                    volume=volume,
                    premium=flow_data.get("premium", 0.0),
                    direction=direction,
                    timestamp=datetime.fromisoformat(flow_data.get("timestamp", "")),
                    unusual=flow_data.get("unusual", False),
                    sentiment_score=sentiment_score
                ))
            
            return flows
        except Exception as e:
            logger.error(f"Error getting options flow for {symbol}: {e}")
            return []
    
    async def get_flow_ratio(self, symbol: str, hours: int = 24) -> float:
        """Get bullish flow ratio for a symbol"""
        try:
            flows = await self.get_options_flow(symbol, hours)
            
            if not flows:
                return 0.0
            
            bullish_volume = sum(f.volume for f in flows if f.direction == FlowDirection.BULLISH)
            bearish_volume = sum(f.volume for f in flows if f.direction == FlowDirection.BEARISH)
            total_volume = bullish_volume + bearish_volume
            
            if total_volume == 0:
                return 0.0
            
            return bullish_volume / total_volume
        except Exception as e:
            logger.error(f"Error getting flow ratio for {symbol}: {e}")
            return 0.0
    
    async def get_call_premium_delta_ma3(self, symbol: str) -> float:
        """Get 3-day moving average of call premium delta"""
        try:
            # Get options flow for the last 3 days
            flows = await self.get_options_flow(symbol, hours=72)
            
            # Filter for call options
            call_flows = [f for f in flows if f.option_type == "call"]
            
            if not call_flows:
                return 0.0
            
            # Calculate daily premium deltas
            daily_premiums = {}
            for flow in call_flows:
                date = flow.timestamp.date()
                if date not in daily_premiums:
                    daily_premiums[date] = []
                daily_premiums[date].append(flow.premium)
            
            # Calculate daily averages and deltas
            daily_averages = {}
            for date, premiums in daily_premiums.items():
                daily_averages[date] = sum(premiums) / len(premiums)
            
            # Calculate 3-day moving average of deltas
            dates = sorted(daily_averages.keys())
            if len(dates) < 2:
                return 0.0
            
            deltas = []
            for i in range(1, len(dates)):
                delta = daily_averages[dates[i]] - daily_averages[dates[i-1]]
                deltas.append(delta)
            
            if len(deltas) >= 3:
                return sum(deltas[-3:]) / 3
            else:
                return sum(deltas) / len(deltas) if deltas else 0.0
                
        except Exception as e:
            logger.error(f"Error getting call premium delta MA3 for {symbol}: {e}")
            return 0.0
    
    async def get_unusual_activity(self, symbol: Optional[str] = None, 
                                 hours: int = 24) -> List[OptionsFlow]:
        """Get unusual options activity"""
        try:
            params = {
                "hours": hours,
                "unusual_only": True
            }
            
            if symbol:
                params["symbol"] = symbol
            
            data = await self._make_request("options/unusual", params)
            
            flows = []
            for flow_data in data.get("flows", []):
                option_type = flow_data.get("type", "").lower()
                volume = flow_data.get("volume", 0)
                
                if option_type == "call" and volume > 0:
                    direction = FlowDirection.BULLISH
                elif option_type == "put" and volume > 0:
                    direction = FlowDirection.BEARISH
                else:
                    direction = FlowDirection.NEUTRAL
                
                sentiment_score = self._calculate_sentiment_score(flow_data)
                
                flows.append(OptionsFlow(
                    symbol=flow_data.get("symbol", ""),
                    strike=flow_data.get("strike", 0.0),
                    expiry=datetime.fromisoformat(flow_data.get("expiry", "")),
                    option_type=option_type,
                    volume=volume,
                    premium=flow_data.get("premium", 0.0),
                    direction=direction,
                    timestamp=datetime.fromisoformat(flow_data.get("timestamp", "")),
                    unusual=True,
                    sentiment_score=sentiment_score
                ))
            
            return flows
        except Exception as e:
            logger.error(f"Error getting unusual activity: {e}")
            return []
    
    async def get_comprehensive_data(self, symbol: str) -> UnusualWhalesData:
        """Get comprehensive Unusual Whales data for a symbol"""
        try:
            # Get all data concurrently
            market_tide_task = asyncio.create_task(self.get_market_tide())
            flow_ratio_task = asyncio.create_task(self.get_flow_ratio(symbol))
            premium_delta_task = asyncio.create_task(self.get_call_premium_delta_ma3(symbol))
            unusual_activity_task = asyncio.create_task(self.get_unusual_activity(symbol))
            
            # Wait for all tasks to complete
            market_tide = await market_tide_task
            flow_ratio = await flow_ratio_task
            call_premium_delta_ma3 = await premium_delta_task
            unusual_activity = await unusual_activity_task
            
            # Calculate overall sentiment score
            sentiment_score = self._calculate_overall_sentiment(
                market_tide.score, flow_ratio, call_premium_delta_ma3
            )
            
            return UnusualWhalesData(
                market_tide=market_tide,
                flow_ratio=flow_ratio,
                call_premium_delta_ma3=call_premium_delta_ma3,
                unusual_activity=unusual_activity,
                sentiment_score=sentiment_score
            )
        except Exception as e:
            logger.error(f"Error getting comprehensive data for {symbol}: {e}")
            # Return neutral data on error
            return UnusualWhalesData(
                market_tide=MarketTide(
                    level=MarketTideLevel.NEUTRAL,
                    score=0.0,
                    timestamp=datetime.now(),
                    description="Error fetching data"
                ),
                flow_ratio=0.5,
                call_premium_delta_ma3=0.0,
                unusual_activity=[],
                sentiment_score=0.0
            )
    
    def _calculate_sentiment_score(self, flow_data: Dict[str, Any]) -> float:
        """Calculate sentiment score for a single flow"""
        option_type = flow_data.get("type", "").lower()
        volume = flow_data.get("volume", 0)
        premium = flow_data.get("premium", 0.0)
        unusual = flow_data.get("unusual", False)
        
        # Base score based on option type
        base_score = 1.0 if option_type == "call" else -1.0
        
        # Adjust for volume (higher volume = stronger signal)
        volume_factor = min(volume / 1000, 2.0)  # Cap at 2x
        
        # Adjust for premium (higher premium = stronger conviction)
        premium_factor = min(premium / 1000000, 2.0)  # Cap at 2x
        
        # Adjust for unusual activity
        unusual_factor = 1.5 if unusual else 1.0
        
        # Calculate final score
        score = base_score * volume_factor * premium_factor * unusual_factor
        
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, score))
    
    def _calculate_overall_sentiment(self, market_tide_score: float, 
                                   flow_ratio: float, premium_delta: float) -> float:
        """Calculate overall sentiment score"""
        # Weight the different factors
        tide_weight = 0.4
        flow_weight = 0.4
        premium_weight = 0.2
        
        # Convert flow ratio to -1 to 1 scale
        flow_score = (flow_ratio - 0.5) * 2
        
        # Normalize premium delta
        premium_score = max(-1.0, min(1.0, premium_delta / 1000000))
        
        # Calculate weighted average
        overall_score = (
            market_tide_score * tide_weight +
            flow_score * flow_weight +
            premium_score * premium_weight
        )
        
        return max(-1.0, min(1.0, overall_score))

class UnusualWhalesManager:
    """Manager for Unusual Whales API with caching and error handling"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def start(self):
        """Start the Unusual Whales manager"""
        self.client = UnusualWhalesClient(self.api_key)
    
    async def stop(self):
        """Stop the Unusual Whales manager"""
        if self.client:
            await self.client.__aexit__(None, None, None)
    
    async def get_data(self, symbol: str, use_cache: bool = True) -> UnusualWhalesData:
        """Get Unusual Whales data with caching"""
        cache_key = f"uw_data_{symbol}"
        
        if use_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return cached_data
        
        if not self.client:
            await self.start()
        
        async with self.client as client:
            data = await client.get_comprehensive_data(symbol)
            
            # Cache the data
            self.cache[cache_key] = (data, datetime.now().timestamp())
            
            return data
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
