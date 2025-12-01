"""
Technical Analyst Agent (T7: Analyst Agents)
=============================================

Analyzes price action and technical indicators to produce trading recommendations.
Uses RSI, MACD, Bollinger Bands, moving averages, and volume analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .base import (
    AnalystAgent,
    AnalystConfidence,
    AnalystRecommendation,
    AnalystReport,
    SignalStrength,
)
from ..strategy.base import TechnicalIndicators

logger = logging.getLogger(__name__)


class TechnicalAnalyst(AnalystAgent):
    """
    Technical analysis agent that evaluates price action and indicators.

    Analyzes:
    - RSI (overbought/oversold)
    - MACD (momentum and crossovers)
    - Bollinger Bands (volatility and mean reversion)
    - Moving averages (trend direction)
    - Volume patterns
    - Support/resistance levels
    """

    def __init__(
        self,
        name: str = "Technical Analyst",
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        sma_periods: List[int] = None,
        bb_period: int = 20,
        bb_std: float = 2.0,
    ):
        """
        Initialize Technical Analyst.

        Args:
            name: Analyst name
            rsi_oversold: RSI level considered oversold (bullish)
            rsi_overbought: RSI level considered overbought (bearish)
            sma_periods: List of SMA periods to analyze (default: [20, 50, 200])
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands standard deviation multiplier
        """
        super().__init__(name=name, analyst_type="technical")

        self.indicators = TechnicalIndicators()
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.sma_periods = sma_periods or [20, 50, 200]
        self.bb_period = bb_period
        self.bb_std = bb_std

    async def analyze(
        self,
        symbol: str,
        data: Optional[pd.DataFrame] = None,
        **kwargs,
    ) -> AnalystReport:
        """
        Analyze a symbol using technical indicators.

        Args:
            symbol: Trading symbol to analyze
            data: OHLCV DataFrame (columns: open, high, low, close, volume)
            **kwargs: Additional parameters

        Returns:
            AnalystReport with technical analysis results
        """
        if data is None or data.empty:
            return self._create_empty_report(symbol, "No price data available")

        if len(data) < max(self.sma_periods):
            return self._create_empty_report(
                symbol, f"Insufficient data (need {max(self.sma_periods)} bars)"
            )

        try:
            # Calculate all indicators
            indicators = self._calculate_indicators(data)

            # Analyze each indicator
            rsi_analysis = self._analyze_rsi(indicators)
            macd_analysis = self._analyze_macd(indicators)
            bb_analysis = self._analyze_bollinger(indicators, data)
            sma_analysis = self._analyze_moving_averages(indicators, data)
            volume_analysis = self._analyze_volume(data)

            # Combine analyses into overall score
            combined = self._combine_analyses(
                rsi_analysis,
                macd_analysis,
                bb_analysis,
                sma_analysis,
                volume_analysis,
            )

            # Build key factors
            key_factors = []
            warnings = []

            if rsi_analysis["signal"] != "neutral":
                key_factors.append(f"RSI {rsi_analysis['signal']}: {rsi_analysis['value']:.1f}")
            if macd_analysis["signal"] != "neutral":
                key_factors.append(f"MACD {macd_analysis['signal']}")
            if bb_analysis["signal"] != "neutral":
                key_factors.append(f"Bollinger {bb_analysis['signal']}")
            if sma_analysis["trend"] != "neutral":
                key_factors.append(f"Trend: {sma_analysis['trend']}")
            if volume_analysis["signal"] != "neutral":
                key_factors.append(f"Volume: {volume_analysis['signal']}")

            # Add warnings
            if rsi_analysis["extreme"]:
                warnings.append(f"RSI at extreme level ({rsi_analysis['value']:.1f})")
            if bb_analysis.get("squeeze"):
                warnings.append("Bollinger Band squeeze detected - potential breakout")
            if volume_analysis.get("unusual"):
                warnings.append("Unusual volume detected")

            # Get current price
            current_price = float(data["close"].iloc[-1])

            # Calculate suggested levels
            suggested_entry = current_price
            suggested_stop_loss = self._calculate_stop_loss(data, combined["bias"])
            suggested_take_profit = self._calculate_take_profit(
                current_price, suggested_stop_loss, combined["bias"]
            )

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
                summary=self._generate_summary(combined, indicators),
                key_factors=key_factors,
                warnings=warnings,
                metrics=indicators,
                raw_data={
                    "rsi_analysis": rsi_analysis,
                    "macd_analysis": macd_analysis,
                    "bb_analysis": bb_analysis,
                    "sma_analysis": sma_analysis,
                    "volume_analysis": volume_analysis,
                },
                suggested_entry=suggested_entry,
                suggested_stop_loss=suggested_stop_loss,
                suggested_take_profit=suggested_take_profit,
                expires_at=datetime.now() + timedelta(hours=4),
                data_freshness_seconds=0.0,
            )

        except Exception as e:
            logger.error(f"Technical analysis error for {symbol}: {e}", exc_info=True)
            return self._create_empty_report(symbol, f"Analysis error: {str(e)}")

    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        close = data["close"]
        high = data["high"]
        low = data["low"]
        volume = data["volume"] if "volume" in data.columns else pd.Series([0] * len(data))

        indicators = {}

        # RSI
        rsi = self.indicators.rsi(close)
        indicators["rsi"] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        indicators["rsi_prev"] = float(rsi.iloc[-2]) if len(rsi) > 1 and not pd.isna(rsi.iloc[-2]) else 50.0

        # MACD (using EMA)
        ema12 = self.indicators.ema(close, 12)
        ema26 = self.indicators.ema(close, 26)
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - signal_line

        indicators["macd"] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0
        indicators["macd_signal"] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0
        indicators["macd_histogram"] = float(macd_histogram.iloc[-1]) if not pd.isna(macd_histogram.iloc[-1]) else 0.0
        indicators["macd_prev"] = float(macd_line.iloc[-2]) if len(macd_line) > 1 else 0.0
        indicators["macd_signal_prev"] = float(signal_line.iloc[-2]) if len(signal_line) > 1 else 0.0

        # Bollinger Bands
        bb = self.indicators.bollinger_bands(close, self.bb_period, self.bb_std)
        indicators["bb_upper"] = float(bb["upper"].iloc[-1]) if not pd.isna(bb["upper"].iloc[-1]) else close.iloc[-1]
        indicators["bb_lower"] = float(bb["lower"].iloc[-1]) if not pd.isna(bb["lower"].iloc[-1]) else close.iloc[-1]
        indicators["bb_middle"] = float(bb["middle"].iloc[-1]) if not pd.isna(bb["middle"].iloc[-1]) else close.iloc[-1]
        indicators["bb_width"] = (indicators["bb_upper"] - indicators["bb_lower"]) / indicators["bb_middle"]

        # Moving Averages
        for period in self.sma_periods:
            sma = self.indicators.sma(close, period)
            indicators[f"sma_{period}"] = float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else close.iloc[-1]

        # ATR for volatility
        atr = self.indicators.atr(high, low, close)
        indicators["atr"] = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
        indicators["atr_pct"] = indicators["atr"] / float(close.iloc[-1]) * 100

        # Volume
        indicators["volume"] = float(volume.iloc[-1]) if not pd.isna(volume.iloc[-1]) else 0.0
        indicators["volume_sma"] = float(volume.rolling(20).mean().iloc[-1]) if len(volume) >= 20 else indicators["volume"]
        indicators["volume_ratio"] = indicators["volume"] / indicators["volume_sma"] if indicators["volume_sma"] > 0 else 1.0

        # Current price
        indicators["price"] = float(close.iloc[-1])

        return indicators

    def _analyze_rsi(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze RSI indicator"""
        rsi = indicators["rsi"]
        rsi_prev = indicators["rsi_prev"]

        analysis = {
            "value": rsi,
            "signal": "neutral",
            "score": 0.0,
            "extreme": False,
        }

        if rsi <= self.rsi_oversold:
            analysis["signal"] = "oversold"
            analysis["score"] = (self.rsi_oversold - rsi) / self.rsi_oversold
            analysis["extreme"] = rsi < 20
        elif rsi >= self.rsi_overbought:
            analysis["signal"] = "overbought"
            analysis["score"] = -(rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
            analysis["extreme"] = rsi > 80
        else:
            # Normalize RSI to -1 to 1 range centered at 50
            analysis["score"] = (rsi - 50) / 50 * 0.3  # Reduced weight when not extreme

        # Check for divergence (RSI moving opposite to price)
        analysis["momentum"] = "rising" if rsi > rsi_prev else "falling" if rsi < rsi_prev else "flat"

        return analysis

    def _analyze_macd(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze MACD indicator"""
        macd = indicators["macd"]
        signal = indicators["macd_signal"]
        histogram = indicators["macd_histogram"]
        macd_prev = indicators["macd_prev"]
        signal_prev = indicators["macd_signal_prev"]

        analysis = {
            "value": macd,
            "signal": "neutral",
            "score": 0.0,
            "crossover": False,
        }

        # Check for crossover
        if macd_prev <= signal_prev and macd > signal:
            analysis["signal"] = "bullish_crossover"
            analysis["score"] = 0.6
            analysis["crossover"] = True
        elif macd_prev >= signal_prev and macd < signal:
            analysis["signal"] = "bearish_crossover"
            analysis["score"] = -0.6
            analysis["crossover"] = True
        elif macd > signal:
            analysis["signal"] = "bullish"
            # Score based on histogram strength
            analysis["score"] = min(0.4, histogram * 10) if histogram > 0 else 0.2
        elif macd < signal:
            analysis["signal"] = "bearish"
            analysis["score"] = max(-0.4, histogram * 10) if histogram < 0 else -0.2

        # Histogram trend
        analysis["histogram_trend"] = "expanding" if abs(histogram) > abs(indicators.get("macd_histogram_prev", histogram)) else "contracting"

        return analysis

    def _analyze_bollinger(self, indicators: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze Bollinger Bands"""
        price = indicators["price"]
        upper = indicators["bb_upper"]
        lower = indicators["bb_lower"]
        middle = indicators["bb_middle"]
        width = indicators["bb_width"]

        analysis = {
            "signal": "neutral",
            "score": 0.0,
            "position": "middle",
            "squeeze": False,
        }

        # Check for squeeze (low volatility)
        # Compare current width to historical average
        if width < 0.04:  # Less than 4% width indicates potential squeeze
            analysis["squeeze"] = True

        # Position relative to bands
        band_range = upper - lower
        if band_range > 0:
            position = (price - lower) / band_range

            if position > 0.95:  # Near or above upper band
                analysis["signal"] = "overbought"
                analysis["score"] = -0.4 * (position - 0.5)
                analysis["position"] = "upper"
            elif position < 0.05:  # Near or below lower band
                analysis["signal"] = "oversold"
                analysis["score"] = 0.4 * (0.5 - position)
                analysis["position"] = "lower"
            elif position > 0.7:
                analysis["signal"] = "high"
                analysis["score"] = -0.2
                analysis["position"] = "upper_half"
            elif position < 0.3:
                analysis["signal"] = "low"
                analysis["score"] = 0.2
                analysis["position"] = "lower_half"

        return analysis

    def _analyze_moving_averages(self, indicators: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze moving average relationships"""
        price = indicators["price"]

        analysis = {
            "trend": "neutral",
            "score": 0.0,
            "above_smas": 0,
            "below_smas": 0,
        }

        sma_values = []
        for period in self.sma_periods:
            sma_key = f"sma_{period}"
            if sma_key in indicators:
                sma_val = indicators[sma_key]
                sma_values.append((period, sma_val))

                if price > sma_val:
                    analysis["above_smas"] += 1
                else:
                    analysis["below_smas"] += 1

        if not sma_values:
            return analysis

        # Determine trend
        total_smas = len(sma_values)
        above_ratio = analysis["above_smas"] / total_smas

        if above_ratio >= 0.8:
            analysis["trend"] = "strong_bullish"
            analysis["score"] = 0.5
        elif above_ratio >= 0.6:
            analysis["trend"] = "bullish"
            analysis["score"] = 0.3
        elif above_ratio <= 0.2:
            analysis["trend"] = "strong_bearish"
            analysis["score"] = -0.5
        elif above_ratio <= 0.4:
            analysis["trend"] = "bearish"
            analysis["score"] = -0.3

        # Check for golden/death cross (50 vs 200 SMA)
        if "sma_50" in indicators and "sma_200" in indicators:
            sma_50 = indicators["sma_50"]
            sma_200 = indicators["sma_200"]

            if sma_50 > sma_200:
                analysis["cross"] = "golden"
                analysis["score"] += 0.1
            else:
                analysis["cross"] = "death"
                analysis["score"] -= 0.1

        return analysis

    def _analyze_volume(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns"""
        if "volume" not in data.columns:
            return {"signal": "neutral", "score": 0.0, "unusual": False}

        volume = data["volume"]
        current_vol = float(volume.iloc[-1])

        analysis = {
            "signal": "neutral",
            "score": 0.0,
            "unusual": False,
            "current": current_vol,
        }

        if len(volume) < 20:
            return analysis

        avg_volume = float(volume.rolling(20).mean().iloc[-1])
        if avg_volume > 0:
            volume_ratio = current_vol / avg_volume

            if volume_ratio > 2.0:
                analysis["unusual"] = True
                analysis["signal"] = "high_volume"
                # High volume confirms the trend
                price_change = float(data["close"].iloc[-1]) - float(data["close"].iloc[-2])
                if price_change > 0:
                    analysis["score"] = 0.2
                else:
                    analysis["score"] = -0.2
            elif volume_ratio < 0.5:
                analysis["signal"] = "low_volume"
                # Low volume suggests weak conviction

        return analysis

    def _combine_analyses(
        self,
        rsi: Dict[str, Any],
        macd: Dict[str, Any],
        bb: Dict[str, Any],
        sma: Dict[str, Any],
        volume: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Combine individual analyses into overall score"""
        # Weighted combination
        weights = {
            "rsi": 0.2,
            "macd": 0.25,
            "bb": 0.15,
            "sma": 0.3,
            "volume": 0.1,
        }

        total_score = (
            rsi["score"] * weights["rsi"]
            + macd["score"] * weights["macd"]
            + bb["score"] * weights["bb"]
            + sma["score"] * weights["sma"]
            + volume["score"] * weights["volume"]
        )

        # Clip to -1 to 1 range
        total_score = max(-1.0, min(1.0, total_score))

        # Calculate confidence based on indicator agreement
        scores = [rsi["score"], macd["score"], bb["score"], sma["score"]]
        signs = [1 if s > 0 else -1 if s < 0 else 0 for s in scores]
        agreement = abs(sum(signs)) / len(signs)

        # Higher agreement = higher confidence
        confidence = 0.3 + (agreement * 0.5)

        # Boost confidence for extreme readings
        if rsi["extreme"] or macd["crossover"]:
            confidence = min(1.0, confidence + 0.15)

        return {
            "score": total_score,
            "bias": total_score,
            "confidence": confidence,
            "agreement": agreement,
        }

    def _calculate_stop_loss(self, data: pd.DataFrame, bias: float) -> Optional[float]:
        """Calculate suggested stop loss based on ATR"""
        if "high" not in data.columns or "low" not in data.columns:
            return None

        atr = self.indicators.atr(data["high"], data["low"], data["close"])
        current_atr = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
        current_price = float(data["close"].iloc[-1])

        if current_atr == 0:
            return None

        # 2x ATR stop loss
        if bias > 0:  # Bullish - stop below
            return current_price - (2 * current_atr)
        else:  # Bearish - stop above
            return current_price + (2 * current_atr)

    def _calculate_take_profit(
        self, current_price: float, stop_loss: Optional[float], bias: float
    ) -> Optional[float]:
        """Calculate suggested take profit (2:1 risk/reward)"""
        if stop_loss is None:
            return None

        risk = abs(current_price - stop_loss)
        reward = risk * 2

        if bias > 0:  # Bullish
            return current_price + reward
        else:  # Bearish
            return current_price - reward

    def _generate_summary(self, combined: Dict[str, Any], indicators: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        score = combined["score"]
        confidence = combined["confidence"]

        if score >= 0.4:
            direction = "strongly bullish"
        elif score >= 0.2:
            direction = "moderately bullish"
        elif score >= 0.05:
            direction = "slightly bullish"
        elif score <= -0.4:
            direction = "strongly bearish"
        elif score <= -0.2:
            direction = "moderately bearish"
        elif score <= -0.05:
            direction = "slightly bearish"
        else:
            direction = "neutral"

        rsi = indicators.get("rsi", 50)
        price = indicators.get("price", 0)

        return (
            f"Technical analysis is {direction}. "
            f"RSI at {rsi:.1f}, price at ${price:.2f}. "
            f"Confidence: {confidence * 100:.0f}%"
        )
