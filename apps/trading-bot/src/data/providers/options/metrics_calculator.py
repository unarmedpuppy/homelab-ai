"""
Options Metrics Calculator
==========================

Calculates various options metrics including put/call ratios, 
volume metrics, and flow statistics.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass

from ..unusual_whales import OptionsFlow, FlowDirection

logger = logging.getLogger(__name__)


@dataclass
class PutCallRatios:
    """Put/Call ratio metrics"""
    volume_ratio: float  # Put volume / Call volume
    premium_ratio: float  # Put premium / Call premium
    oi_ratio: Optional[float] = None  # Put OI / Call OI
    timestamp: datetime = None


@dataclass
class FlowMetrics:
    """Options flow metrics"""
    total_volume: int
    total_premium: float
    call_volume: int
    put_volume: int
    call_premium: float
    put_premium: float
    bullish_flow: float  # -1 to 1
    bearish_flow: float  # -1 to 1
    unusual_count: int
    sweep_count: int
    block_count: int


class OptionsMetricsCalculator:
    """
    Calculator for options flow metrics
    """
    
    def calculate_put_call_ratio(
        self,
        flows: List[OptionsFlow],
        use_premium: bool = True,
        use_volume: bool = True
    ) -> PutCallRatios:
        """
        Calculate put/call ratio
        
        Args:
            flows: List of options flows
            use_premium: Calculate premium-based ratio
            use_volume: Calculate volume-based ratio
            
        Returns:
            PutCallRatios object
        """
        call_volume = sum(f.volume for f in flows if f.option_type == "call")
        put_volume = sum(f.volume for f in flows if f.option_type == "put")
        call_premium = sum(f.premium for f in flows if f.option_type == "call")
        put_premium = sum(f.premium for f in flows if f.option_type == "put")
        
        # Volume ratio
        volume_ratio = put_volume / call_volume if call_volume > 0 else float('inf')
        
        # Premium ratio
        premium_ratio = put_premium / call_premium if call_premium > 0 else float('inf')
        
        # OI ratio (if available)
        call_oi = sum(f.open_interest or 0 for f in flows if f.option_type == "call")
        put_oi = sum(f.open_interest or 0 for f in flows if f.option_type == "put")
        oi_ratio = put_oi / call_oi if call_oi > 0 else None
        
        return PutCallRatios(
            volume_ratio=volume_ratio if use_volume else 0.0,
            premium_ratio=premium_ratio if use_premium else 0.0,
            oi_ratio=oi_ratio,
            timestamp=datetime.now()
        )
    
    def calculate_put_call_ratios_timeframe(
        self,
        flows: List[OptionsFlow],
        timeframes: List[int]  # Hours
    ) -> Dict[int, PutCallRatios]:
        """
        Calculate put/call ratios for multiple timeframes
        
        Args:
            flows: List of all flows
            timeframes: List of hour windows
            
        Returns:
            Dictionary mapping timeframe (hours) to PutCallRatios
        """
        now = datetime.now()
        ratios = {}
        
        for hours in timeframes:
            cutoff = now - timedelta(hours=hours)
            timeframe_flows = [f for f in flows if f.timestamp >= cutoff]
            
            ratios[hours] = self.calculate_put_call_ratio(timeframe_flows)
        
        return ratios
    
    def calculate_flow_metrics(self, flows: List[OptionsFlow]) -> FlowMetrics:
        """
        Calculate comprehensive flow metrics
        
        Args:
            flows: List of options flows
            
        Returns:
            FlowMetrics object
        """
        call_flows = [f for f in flows if f.option_type == "call"]
        put_flows = [f for f in flows if f.option_type == "put"]
        
        total_volume = sum(f.volume for f in flows)
        total_premium = sum(f.premium for f in flows)
        call_volume = sum(f.volume for f in call_flows)
        put_volume = sum(f.volume for f in put_flows)
        call_premium = sum(f.premium for f in call_flows)
        put_premium = sum(f.premium for f in put_flows)
        
        # Calculate bullish/bearish flow scores
        bullish_volume = sum(f.volume for f in flows if f.direction == FlowDirection.BULLISH)
        bearish_volume = sum(f.volume for f in flows if f.direction == FlowDirection.BEARISH)
        
        total_directional_volume = bullish_volume + bearish_volume
        if total_directional_volume > 0:
            bullish_flow = bullish_volume / total_directional_volume
            bearish_flow = bearish_volume / total_directional_volume
        else:
            bullish_flow = 0.5
            bearish_flow = 0.5
        
        # Count patterns
        unusual_count = sum(1 for f in flows if f.unusual)
        sweep_count = sum(1 for f in flows if f.is_sweep)
        block_count = sum(1 for f in flows if f.is_block)
        
        return FlowMetrics(
            total_volume=total_volume,
            total_premium=total_premium,
            call_volume=call_volume,
            put_volume=put_volume,
            call_premium=call_premium,
            put_premium=put_premium,
            bullish_flow=bullish_flow,
            bearish_flow=bearish_flow,
            unusual_count=unusual_count,
            sweep_count=sweep_count,
            block_count=block_count
        )

