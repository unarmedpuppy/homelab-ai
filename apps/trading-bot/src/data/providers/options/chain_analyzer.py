"""
Options Chain Analyzer
======================

Analyzes options chains for max pain, gamma exposure, and strike concentration.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
import math

from ..unusual_whales import OptionsFlow

logger = logging.getLogger(__name__)


@dataclass
class ChainAnalysis:
    """Options chain analysis results"""
    max_pain: float  # Strike price with max pain
    gamma_exposure: float  # Net gamma exposure
    call_dominance: float  # Ratio of call to put open interest
    put_dominance: float  # Ratio of put to call open interest
    strike_concentration: Dict[float, float]  # Strike -> OI percentage
    high_volume_strikes: List[Tuple[float, int]]  # (strike, volume)


class OptionsChainAnalyzer:
    """
    Analyzes options chains for various metrics
    """
    
    def analyze_chain(
        self,
        flows: List[OptionsFlow],
        current_price: Optional[float] = None
    ) -> ChainAnalysis:
        """
        Analyze options chain from flows
        
        Args:
            flows: List of options flows
            current_price: Current stock price (for GEX calculation)
            
        Returns:
            ChainAnalysis object
        """
        # Group by strike
        call_oi_by_strike = defaultdict(int)
        put_oi_by_strike = defaultdict(int)
        call_volume_by_strike = defaultdict(int)
        put_volume_by_strike = defaultdict(int)
        
        for flow in flows:
            strike = flow.strike
            oi = flow.open_interest or 0
            
            if flow.option_type == "call":
                call_oi_by_strike[strike] += oi
                call_volume_by_strike[strike] += flow.volume
            else:
                put_oi_by_strike[strike] += oi
                put_volume_by_strike[strike] += flow.volume
        
        # Calculate max pain
        max_pain = self._calculate_max_pain(call_oi_by_strike, put_oi_by_strike)
        
        # Calculate gamma exposure (simplified)
        gamma_exposure = self._calculate_gamma_exposure(
            call_oi_by_strike,
            put_oi_by_strike,
            current_price
        )
        
        # Calculate dominance ratios
        total_call_oi = sum(call_oi_by_strike.values())
        total_put_oi = sum(put_oi_by_strike.values())
        total_oi = total_call_oi + total_put_oi
        
        call_dominance = total_call_oi / total_oi if total_oi > 0 else 0.0
        put_dominance = total_put_oi / total_oi if total_oi > 0 else 0.0
        
        # Strike concentration
        all_strikes = set(call_oi_by_strike.keys()) | set(put_oi_by_strike.keys())
        strike_concentration = {}
        for strike in all_strikes:
            strike_oi = call_oi_by_strike[strike] + put_oi_by_strike[strike]
            strike_concentration[strike] = strike_oi / total_oi if total_oi > 0 else 0.0
        
        # High volume strikes
        all_volumes = {}
        for strike in all_strikes:
            all_volumes[strike] = (
                call_volume_by_strike[strike] + put_volume_by_strike[strike]
            )
        high_volume_strikes = sorted(
            [(s, v) for s, v in all_volumes.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10
        
        return ChainAnalysis(
            max_pain=max_pain,
            gamma_exposure=gamma_exposure,
            call_dominance=call_dominance,
            put_dominance=put_dominance,
            strike_concentration=strike_concentration,
            high_volume_strikes=high_volume_strikes
        )
    
    def _calculate_max_pain(
        self,
        call_oi: Dict[float, int],
        put_oi: Dict[float, int]
    ) -> float:
        """
        Calculate max pain strike
        
        Max pain is the strike price where option holders would lose the most
        (where total option value would be minimized at expiration).
        
        Args:
            call_oi: Call open interest by strike
            put_oi: Put open interest by strike
            
        Returns:
            Max pain strike price
        """
        all_strikes = sorted(set(call_oi.keys()) | set(put_oi.keys()))
        
        if not all_strikes:
            return 0.0
        
        min_pain = float('inf')
        max_pain_strike = all_strikes[0]
        
        for strike_price in all_strikes:
            total_pain = 0.0
            
            # Pain from calls (if stock < strike, call holders lose)
            for s, oi in call_oi.items():
                if s < strike_price:
                    total_pain += oi * (strike_price - s)
            
            # Pain from puts (if stock > strike, put holders lose)
            for s, oi in put_oi.items():
                if s > strike_price:
                    total_pain += oi * (s - strike_price)
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = strike_price
        
        return max_pain_strike
    
    def _calculate_gamma_exposure(
        self,
        call_oi: Dict[float, int],
        put_oi: Dict[float, int],
        current_price: Optional[float]
    ) -> float:
        """
        Calculate simplified gamma exposure
        
        Note: Full GEX calculation requires detailed Greeks. This is a simplified
        approximation based on open interest concentration.
        
        Args:
            call_oi: Call open interest by strike
            put_oi: Put open interest by strike
            current_price: Current stock price
            
        Returns:
            Net gamma exposure (simplified)
        """
        if current_price is None:
            return 0.0
        
        net_gex = 0.0
        
        # Simplified: Calls add positive gamma, puts add negative gamma
        # Weighted by distance from current price
        for strike, oi in call_oi.items():
            distance = abs(strike - current_price) / current_price if current_price > 0 else 1.0
            weight = 1.0 / (1.0 + distance * 10)  # Closer strikes weighted more
            net_gex += oi * weight
        
        for strike, oi in put_oi.items():
            distance = abs(strike - current_price) / current_price if current_price > 0 else 1.0
            weight = 1.0 / (1.0 + distance * 10)
            net_gex -= oi * weight
        
        return net_gex

