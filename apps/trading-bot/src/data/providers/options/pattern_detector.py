"""
Options Pattern Detector
========================

Detects options flow patterns including sweeps, blocks, and spreads.
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..unusual_whales import OptionsFlow, FlowDirection

logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Detects patterns in options flow data
    
    Patterns detected:
    - Sweeps: Multiple strikes executed simultaneously
    - Blocks: Large single orders
    - Spreads: Coordinated multi-leg trades
    """
    
    def __init__(
        self,
        sweep_time_window_seconds: int = 60,
        sweep_min_strikes: int = 3,
        sweep_min_total_premium: float = 100000.0,
        block_min_premium: float = 500000.0,
        block_min_volume: int = 1000
    ):
        """
        Initialize pattern detector
        
        Args:
            sweep_time_window_seconds: Time window to group sweeps (default: 60s)
            sweep_min_strikes: Minimum strikes for sweep (default: 3)
            sweep_min_total_premium: Minimum total premium for sweep (default: $100k)
            block_min_premium: Minimum premium for block (default: $500k)
            block_min_volume: Minimum volume for block (default: 1000)
        """
        self.sweep_time_window = timedelta(seconds=sweep_time_window_seconds)
        self.sweep_min_strikes = sweep_min_strikes
        self.sweep_min_total_premium = sweep_min_total_premium
        self.block_min_premium = block_min_premium
        self.block_min_volume = block_min_volume
    
    def detect_patterns(self, flows: List[OptionsFlow]) -> List[OptionsFlow]:
        """
        Detect patterns in options flows and mark them
        
        Args:
            flows: List of options flows
            
        Returns:
            List of flows with pattern information populated
        """
        # Sort flows by timestamp
        sorted_flows = sorted(flows, key=lambda f: f.timestamp)
        
        # Detect sweeps
        sweeps = self._detect_sweeps(sorted_flows)
        
        # Detect blocks
        blocks = self._detect_blocks(sorted_flows)
        
        # Mark flows with pattern information
        for flow in sorted_flows:
            # Check if part of a sweep
            for sweep in sweeps:
                if flow in sweep['flows']:
                    flow.is_sweep = True
                    flow.pattern_type = "sweep"
                    flow.sweep_strength = sweep['strength']
                    break
            
            # Check if a block
            if flow in blocks:
                flow.is_block = True
                if not flow.pattern_type:
                    flow.pattern_type = "block"
        
        return sorted_flows
    
    def _detect_sweeps(self, flows: List[OptionsFlow]) -> List[Dict]:
        """
        Detect sweep patterns
        
        Sweeps are multiple strikes executed within a short time window,
        often indicating institutional or algorithmic trading.
        
        Args:
            flows: Sorted list of flows
            
        Returns:
            List of sweep dictionaries with flows and metadata
        """
        sweeps = []
        
        # Group flows by symbol and expiry
        grouped = defaultdict(lambda: defaultdict(list))
        for flow in flows:
            key = (flow.symbol, flow.expiry.date(), flow.option_type)
            grouped[key][flow.timestamp].append(flow)
        
        # Detect sweeps within each group
        for (symbol, expiry_date, option_type), time_groups in grouped.items():
            timestamps = sorted(time_groups.keys())
            
            i = 0
            while i < len(timestamps):
                # Look for sweeps starting at this timestamp
                window_start = timestamps[i]
                window_end = window_start + self.sweep_time_window
                
                # Collect flows in this window
                window_flows = []
                for ts in timestamps[i:]:
                    if ts <= window_end:
                        window_flows.extend(time_groups[ts])
                    else:
                        break
                
                # Check if this qualifies as a sweep
                if len(window_flows) >= self.sweep_min_strikes:
                    strikes = set(f.strike for f in window_flows)
                    if len(strikes) >= self.sweep_min_strikes:
                        total_premium = sum(f.premium for f in window_flows)
                        
                        if total_premium >= self.sweep_min_total_premium:
                            # Calculate sweep strength
                            strength = self._calculate_sweep_strength(window_flows)
                            
                            sweeps.append({
                                'flows': window_flows,
                                'symbol': symbol,
                                'expiry': expiry_date,
                                'option_type': option_type,
                                'strike_count': len(strikes),
                                'total_premium': total_premium,
                                'strength': strength,
                                'timestamp': window_start
                            })
                            
                            # Skip ahead past this window
                            j = i + 1
                            while j < len(timestamps) and timestamps[j] <= window_end:
                                j += 1
                            i = j
                            continue
                
                i += 1
        
        return sweeps
    
    def _detect_blocks(self, flows: List[OptionsFlow]) -> List[OptionsFlow]:
        """
        Detect block trades
        
        Blocks are large single orders, typically from institutions.
        
        Args:
            flows: List of flows
            
        Returns:
            List of flows that are blocks
        """
        blocks = []
        
        for flow in flows:
            # Check if flow qualifies as a block
            if (flow.premium >= self.block_min_premium and 
                flow.volume >= self.block_min_volume):
                blocks.append(flow)
        
        return blocks
    
    def _calculate_sweep_strength(self, flows: List[OptionsFlow]) -> float:
        """
        Calculate sweep strength score (0.0 to 1.0)
        
        Factors:
        - Number of strikes (more = stronger)
        - Total premium (higher = stronger)
        - Volume concentration (more concentrated = stronger)
        - Time concentration (tighter window = stronger)
        
        Args:
            flows: Flows in the sweep
            
        Returns:
            Strength score between 0.0 and 1.0
        """
        if not flows:
            return 0.0
        
        strike_count = len(set(f.strike for f in flows))
        total_premium = sum(f.premium for f in flows)
        total_volume = sum(f.volume for f in flows)
        
        # Time span
        timestamps = [f.timestamp for f in flows]
        time_span = (max(timestamps) - min(timestamps)).total_seconds()
        
        # Normalize factors
        strike_score = min(strike_count / 10.0, 1.0)  # Max at 10 strikes
        premium_score = min(total_premium / 1000000.0, 1.0)  # Max at $1M
        volume_score = min(total_volume / 10000.0, 1.0)  # Max at 10k volume
        time_score = 1.0 - min(time_span / 300.0, 1.0)  # Prefer < 5 min
        
        # Weighted average
        strength = (
            strike_score * 0.3 +
            premium_score * 0.3 +
            volume_score * 0.2 +
            time_score * 0.2
        )
        
        return min(1.0, max(0.0, strength))


def detect_sweeps(flows: List[OptionsFlow], **kwargs) -> List[Dict]:
    """
    Convenience function to detect sweeps
    
    Args:
        flows: List of options flows
        **kwargs: PatternDetector initialization parameters
        
    Returns:
        List of sweep dictionaries
    """
    detector = PatternDetector(**kwargs)
    detector.detect_patterns(flows)
    return detector._detect_sweeps(sorted(flows, key=lambda f: f.timestamp))


def detect_blocks(flows: List[OptionsFlow], **kwargs) -> List[OptionsFlow]:
    """
    Convenience function to detect blocks
    
    Args:
        flows: List of options flows
        **kwargs: PatternDetector initialization parameters
        
    Returns:
        List of block flows
    """
    detector = PatternDetector(**kwargs)
    detector.detect_patterns(flows)
    return detector._detect_blocks(sorted(flows, key=lambda f: f.timestamp))

