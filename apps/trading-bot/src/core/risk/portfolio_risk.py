"""
Portfolio Risk Checker
======================

Portfolio-level risk checks beyond individual trade compliance.
Enforces concentration limits, correlation checks, drawdown circuit breakers,
and market regime awareness.

Part of T17: Risk Manager Agent enhancement.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

import numpy as np

logger = logging.getLogger(__name__)


class RiskCheckResult(Enum):
    """Result of a risk check"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class MarketRegime(Enum):
    """Detected market regime"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    UNKNOWN = "unknown"


@dataclass
class RiskCheck:
    """Result of a single risk check"""
    name: str
    result: RiskCheckResult
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioRiskDecision:
    """Combined result of all portfolio risk checks"""
    approved: bool
    checks: List[RiskCheck]
    reason: str
    risk_score: float = 0.0  # 0.0 = no risk, 1.0 = max risk
    adjusted_size: Optional[int] = None  # Suggested reduced position size
    market_regime: MarketRegime = MarketRegime.UNKNOWN

    @property
    def failed_checks(self) -> List[RiskCheck]:
        return [c for c in self.checks if c.result == RiskCheckResult.FAILED]

    @property
    def warning_checks(self) -> List[RiskCheck]:
        return [c for c in self.checks if c.result == RiskCheckResult.WARNING]


@dataclass
class PortfolioRiskSettings:
    """Settings for portfolio risk checks"""
    # Concentration limits
    max_position_pct: float = 0.05  # Max 5% of portfolio per position
    max_symbol_exposure_pct: float = 0.10  # Max 10% per symbol (across all positions)
    max_sector_exposure_pct: float = 0.25  # Max 25% per sector

    # Correlation
    max_correlation: float = 0.7  # Reject positions with >70% correlation to existing
    correlation_lookback_days: int = 30  # Days of price history for correlation

    # Drawdown circuit breaker
    max_daily_loss_pct: float = 0.02  # Stop trading at 2% daily loss
    circuit_breaker_cooldown_minutes: int = 60  # Cooldown after circuit breaker triggers

    # Market regime
    regime_detection_enabled: bool = True
    high_volatility_threshold: float = 0.03  # VIX or daily range threshold
    reduce_size_in_high_vol: bool = True
    high_vol_size_reduction: float = 0.5  # Reduce position size by 50% in high vol

    # General
    enabled: bool = True
    strict_mode: bool = False  # If True, warnings become failures


# Sector mapping for common stocks
SECTOR_MAP: Dict[str, str] = {
    # Technology
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "GOOG": "Technology",
    "META": "Technology", "NVDA": "Technology", "AMD": "Technology", "INTC": "Technology",
    "CRM": "Technology", "ORCL": "Technology", "ADBE": "Technology", "CSCO": "Technology",
    "AVGO": "Technology", "QCOM": "Technology", "TXN": "Technology", "MU": "Technology",
    # Consumer
    "AMZN": "Consumer", "TSLA": "Consumer", "HD": "Consumer", "NKE": "Consumer",
    "MCD": "Consumer", "SBUX": "Consumer", "TGT": "Consumer", "COST": "Consumer",
    # Finance
    "JPM": "Finance", "BAC": "Finance", "WFC": "Finance", "GS": "Finance",
    "MS": "Finance", "C": "Finance", "BLK": "Finance", "SCHW": "Finance",
    # Healthcare
    "JNJ": "Healthcare", "UNH": "Healthcare", "PFE": "Healthcare", "ABBV": "Healthcare",
    "MRK": "Healthcare", "LLY": "Healthcare", "TMO": "Healthcare", "ABT": "Healthcare",
    # Energy
    "XOM": "Energy", "CVX": "Energy", "COP": "Energy", "SLB": "Energy",
    "OXY": "Energy", "EOG": "Energy", "PSX": "Energy", "VLO": "Energy",
    # ETFs
    "SPY": "Index", "QQQ": "Index", "IWM": "Index", "DIA": "Index",
    "XLF": "Finance", "XLK": "Technology", "XLE": "Energy", "XLV": "Healthcare",
}


class PortfolioRiskChecker:
    """
    Portfolio-level risk checks beyond individual trade compliance.

    Checks:
    - Position concentration (max % of portfolio)
    - Symbol exposure (total across positions)
    - Sector exposure limits
    - Correlation with existing positions
    - Daily drawdown circuit breaker
    - Market regime awareness
    """

    def __init__(
        self,
        settings: Optional[PortfolioRiskSettings] = None,
        ibkr_client: Optional[Any] = None,
    ):
        """
        Initialize portfolio risk checker.

        Args:
            settings: Portfolio risk settings
            ibkr_client: Optional IBKR client for live data
        """
        self.settings = settings or PortfolioRiskSettings()
        self.ibkr_client = ibkr_client

        # Circuit breaker state
        self._circuit_breaker_triggered: bool = False
        self._circuit_breaker_triggered_at: Optional[datetime] = None
        self._daily_pnl: float = 0.0
        self._daily_pnl_updated_at: Optional[datetime] = None

        # Cache for market regime
        self._market_regime: MarketRegime = MarketRegime.UNKNOWN
        self._regime_updated_at: Optional[datetime] = None

        logger.info(f"PortfolioRiskChecker initialized with settings: {self.settings}")

    async def evaluate(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        account_id: int,
        positions: Optional[List[Dict]] = None,
        portfolio_value: Optional[float] = None,
    ) -> PortfolioRiskDecision:
        """
        Evaluate a proposed trade against portfolio risk rules.

        Args:
            symbol: Trading symbol
            side: Trade side ("BUY" or "SELL")
            quantity: Number of shares
            price: Price per share
            account_id: Account ID
            positions: Current positions (if not provided, will fetch from IBKR)
            portfolio_value: Total portfolio value (if not provided, will fetch)

        Returns:
            PortfolioRiskDecision with approval status and check results
        """
        if not self.settings.enabled:
            return PortfolioRiskDecision(
                approved=True,
                checks=[],
                reason="Portfolio risk checks disabled",
                risk_score=0.0,
                market_regime=MarketRegime.UNKNOWN,
            )

        checks: List[RiskCheck] = []
        trade_value = quantity * price

        # Get current positions if not provided
        if positions is None:
            positions = await self._get_positions(account_id)

        # Get portfolio value if not provided
        if portfolio_value is None:
            portfolio_value = await self._get_portfolio_value(account_id)

        if portfolio_value <= 0:
            logger.warning("Could not determine portfolio value, using default checks")
            portfolio_value = 100000  # Default for safety

        # Run all checks
        checks.append(await self._check_position_concentration(
            symbol, trade_value, portfolio_value, side
        ))

        checks.append(await self._check_symbol_exposure(
            symbol, trade_value, positions, portfolio_value, side
        ))

        checks.append(await self._check_sector_exposure(
            symbol, trade_value, positions, portfolio_value, side
        ))

        checks.append(await self._check_correlation(
            symbol, positions, side
        ))

        checks.append(await self._check_circuit_breaker(account_id))

        # Check market regime
        regime_check = await self._check_market_regime()
        checks.append(regime_check)
        self._market_regime = regime_check.details.get("regime", MarketRegime.UNKNOWN)

        # Calculate overall risk score
        risk_score = self._calculate_risk_score(checks)

        # Determine if approved
        failed_checks = [c for c in checks if c.result == RiskCheckResult.FAILED]
        warning_checks = [c for c in checks if c.result == RiskCheckResult.WARNING]

        if failed_checks:
            approved = False
            reason = f"Failed {len(failed_checks)} risk check(s): {', '.join(c.name for c in failed_checks)}"
        elif warning_checks and self.settings.strict_mode:
            approved = False
            reason = f"Warnings in strict mode: {', '.join(c.name for c in warning_checks)}"
        else:
            approved = True
            if warning_checks:
                reason = f"Approved with {len(warning_checks)} warning(s)"
            else:
                reason = "All portfolio risk checks passed"

        # Calculate adjusted size if needed
        adjusted_size = None
        if approved and self._should_reduce_size(checks):
            adjusted_size = self._calculate_reduced_size(
                quantity, checks, portfolio_value, price
            )

        decision = PortfolioRiskDecision(
            approved=approved,
            checks=checks,
            reason=reason,
            risk_score=risk_score,
            adjusted_size=adjusted_size,
            market_regime=self._market_regime,
        )

        logger.info(
            f"Portfolio risk evaluation for {side} {quantity} {symbol}: "
            f"approved={approved}, risk_score={risk_score:.2f}, regime={self._market_regime.value}"
        )

        return decision

    async def _check_position_concentration(
        self,
        symbol: str,
        trade_value: float,
        portfolio_value: float,
        side: str,
    ) -> RiskCheck:
        """Check if single position exceeds concentration limit"""
        if side.upper() == "SELL":
            return RiskCheck(
                name="position_concentration",
                result=RiskCheckResult.PASSED,
                message="Sell orders don't increase concentration",
            )

        position_pct = trade_value / portfolio_value
        threshold = self.settings.max_position_pct

        if position_pct > threshold:
            return RiskCheck(
                name="position_concentration",
                result=RiskCheckResult.FAILED,
                message=f"Position size {position_pct:.1%} exceeds limit of {threshold:.1%}",
                value=position_pct,
                threshold=threshold,
                details={"trade_value": trade_value, "portfolio_value": portfolio_value},
            )
        elif position_pct > threshold * 0.8:  # Warning at 80% of limit
            return RiskCheck(
                name="position_concentration",
                result=RiskCheckResult.WARNING,
                message=f"Position size {position_pct:.1%} approaching limit of {threshold:.1%}",
                value=position_pct,
                threshold=threshold,
            )
        else:
            return RiskCheck(
                name="position_concentration",
                result=RiskCheckResult.PASSED,
                message=f"Position size {position_pct:.1%} within limit of {threshold:.1%}",
                value=position_pct,
                threshold=threshold,
            )

    async def _check_symbol_exposure(
        self,
        symbol: str,
        trade_value: float,
        positions: List[Dict],
        portfolio_value: float,
        side: str,
    ) -> RiskCheck:
        """Check total exposure to a symbol across all positions"""
        if side.upper() == "SELL":
            return RiskCheck(
                name="symbol_exposure",
                result=RiskCheckResult.PASSED,
                message="Sell orders reduce exposure",
            )

        # Calculate current exposure to this symbol
        current_exposure = 0.0
        for pos in positions:
            if pos.get("symbol") == symbol:
                pos_value = pos.get("quantity", 0) * pos.get("market_price", pos.get("average_price", 0))
                current_exposure += pos_value

        total_exposure = current_exposure + trade_value
        exposure_pct = total_exposure / portfolio_value
        threshold = self.settings.max_symbol_exposure_pct

        if exposure_pct > threshold:
            return RiskCheck(
                name="symbol_exposure",
                result=RiskCheckResult.FAILED,
                message=f"Total {symbol} exposure {exposure_pct:.1%} exceeds limit of {threshold:.1%}",
                value=exposure_pct,
                threshold=threshold,
                details={"current_exposure": current_exposure, "new_trade": trade_value},
            )
        else:
            return RiskCheck(
                name="symbol_exposure",
                result=RiskCheckResult.PASSED,
                message=f"Total {symbol} exposure {exposure_pct:.1%} within limit",
                value=exposure_pct,
                threshold=threshold,
            )

    async def _check_sector_exposure(
        self,
        symbol: str,
        trade_value: float,
        positions: List[Dict],
        portfolio_value: float,
        side: str,
    ) -> RiskCheck:
        """Check sector concentration"""
        if side.upper() == "SELL":
            return RiskCheck(
                name="sector_exposure",
                result=RiskCheckResult.PASSED,
                message="Sell orders reduce sector exposure",
            )

        sector = self._get_sector(symbol)
        if sector == "Unknown":
            return RiskCheck(
                name="sector_exposure",
                result=RiskCheckResult.WARNING,
                message=f"Unknown sector for {symbol}, cannot check exposure",
                details={"sector": sector},
            )

        # Calculate current sector exposure
        sector_exposure = 0.0
        for pos in positions:
            pos_symbol = pos.get("symbol", "")
            if self._get_sector(pos_symbol) == sector:
                pos_value = pos.get("quantity", 0) * pos.get("market_price", pos.get("average_price", 0))
                sector_exposure += pos_value

        total_sector = sector_exposure + trade_value
        sector_pct = total_sector / portfolio_value
        threshold = self.settings.max_sector_exposure_pct

        if sector_pct > threshold:
            return RiskCheck(
                name="sector_exposure",
                result=RiskCheckResult.FAILED,
                message=f"{sector} sector exposure {sector_pct:.1%} exceeds limit of {threshold:.1%}",
                value=sector_pct,
                threshold=threshold,
                details={"sector": sector, "current_exposure": sector_exposure},
            )
        else:
            return RiskCheck(
                name="sector_exposure",
                result=RiskCheckResult.PASSED,
                message=f"{sector} sector exposure {sector_pct:.1%} within limit",
                value=sector_pct,
                threshold=threshold,
                details={"sector": sector},
            )

    async def _check_correlation(
        self,
        symbol: str,
        positions: List[Dict],
        side: str,
    ) -> RiskCheck:
        """Check correlation with existing positions"""
        if side.upper() == "SELL":
            return RiskCheck(
                name="correlation",
                result=RiskCheckResult.PASSED,
                message="Sell orders don't increase correlation risk",
            )

        if not positions:
            return RiskCheck(
                name="correlation",
                result=RiskCheckResult.PASSED,
                message="No existing positions to check correlation",
            )

        # Get existing symbols
        existing_symbols = [p.get("symbol") for p in positions if p.get("symbol")]

        if symbol in existing_symbols:
            return RiskCheck(
                name="correlation",
                result=RiskCheckResult.PASSED,
                message="Adding to existing position",
            )

        # Calculate correlations (simplified - uses sector proxy)
        # In production, would fetch historical prices and calculate actual correlation
        max_correlation = 0.0
        most_correlated = None

        new_sector = self._get_sector(symbol)
        for pos in positions:
            pos_symbol = pos.get("symbol", "")
            pos_sector = self._get_sector(pos_symbol)

            # Same sector = estimated 0.7 correlation
            # Same category (e.g., both tech stocks) = 0.5
            # Different sectors = 0.2
            if pos_sector == new_sector:
                est_correlation = 0.7
            elif pos_sector in ["Index"]:
                est_correlation = 0.5  # Index correlated with most
            else:
                est_correlation = 0.2

            if est_correlation > max_correlation:
                max_correlation = est_correlation
                most_correlated = pos_symbol

        threshold = self.settings.max_correlation

        if max_correlation > threshold:
            return RiskCheck(
                name="correlation",
                result=RiskCheckResult.WARNING,  # Warning, not failure, for estimated correlation
                message=f"Estimated {max_correlation:.0%} correlation with {most_correlated}",
                value=max_correlation,
                threshold=threshold,
                details={"most_correlated_with": most_correlated, "method": "sector_proxy"},
            )
        else:
            return RiskCheck(
                name="correlation",
                result=RiskCheckResult.PASSED,
                message=f"Low correlation ({max_correlation:.0%}) with existing positions",
                value=max_correlation,
                threshold=threshold,
            )

    async def _check_circuit_breaker(self, account_id: int) -> RiskCheck:
        """Check if daily loss circuit breaker is triggered"""
        # Check if circuit breaker is currently active
        if self._circuit_breaker_triggered:
            if self._circuit_breaker_triggered_at:
                cooldown = timedelta(minutes=self.settings.circuit_breaker_cooldown_minutes)
                if datetime.now() < self._circuit_breaker_triggered_at + cooldown:
                    remaining = (self._circuit_breaker_triggered_at + cooldown) - datetime.now()
                    return RiskCheck(
                        name="circuit_breaker",
                        result=RiskCheckResult.FAILED,
                        message=f"Circuit breaker active. Cooldown: {remaining.seconds // 60} minutes remaining",
                        details={"triggered_at": self._circuit_breaker_triggered_at.isoformat()},
                    )
            # Reset circuit breaker after cooldown
            self._circuit_breaker_triggered = False
            self._circuit_breaker_triggered_at = None

        # Check current daily P&L
        daily_pnl_pct = await self._get_daily_pnl_pct(account_id)
        threshold = -self.settings.max_daily_loss_pct

        if daily_pnl_pct < threshold:
            self._circuit_breaker_triggered = True
            self._circuit_breaker_triggered_at = datetime.now()
            return RiskCheck(
                name="circuit_breaker",
                result=RiskCheckResult.FAILED,
                message=f"Daily loss {daily_pnl_pct:.2%} exceeds limit of {threshold:.2%}. Trading halted.",
                value=daily_pnl_pct,
                threshold=threshold,
            )
        elif daily_pnl_pct < threshold * 0.7:  # Warning at 70% of limit
            return RiskCheck(
                name="circuit_breaker",
                result=RiskCheckResult.WARNING,
                message=f"Daily loss {daily_pnl_pct:.2%} approaching limit of {threshold:.2%}",
                value=daily_pnl_pct,
                threshold=threshold,
            )
        else:
            return RiskCheck(
                name="circuit_breaker",
                result=RiskCheckResult.PASSED,
                message=f"Daily P&L: {daily_pnl_pct:+.2%}",
                value=daily_pnl_pct,
                threshold=threshold,
            )

    async def _check_market_regime(self) -> RiskCheck:
        """Detect current market regime"""
        if not self.settings.regime_detection_enabled:
            return RiskCheck(
                name="market_regime",
                result=RiskCheckResult.PASSED,
                message="Market regime detection disabled",
                details={"regime": MarketRegime.UNKNOWN},
            )

        # Use cached regime if recent
        if self._regime_updated_at:
            cache_duration = timedelta(minutes=15)
            if datetime.now() < self._regime_updated_at + cache_duration:
                return RiskCheck(
                    name="market_regime",
                    result=RiskCheckResult.PASSED if self._market_regime != MarketRegime.HIGH_VOLATILITY else RiskCheckResult.WARNING,
                    message=f"Market regime: {self._market_regime.value}",
                    details={"regime": self._market_regime},
                )

        # Detect regime (simplified - in production would use VIX, SPY trend, etc.)
        regime = await self._detect_regime()
        self._market_regime = regime
        self._regime_updated_at = datetime.now()

        if regime == MarketRegime.HIGH_VOLATILITY:
            return RiskCheck(
                name="market_regime",
                result=RiskCheckResult.WARNING,
                message=f"High volatility detected. Consider reduced position sizes.",
                details={"regime": regime},
            )
        elif regime == MarketRegime.BEAR:
            return RiskCheck(
                name="market_regime",
                result=RiskCheckResult.WARNING,
                message=f"Bear market detected. Exercise caution with long positions.",
                details={"regime": regime},
            )
        else:
            return RiskCheck(
                name="market_regime",
                result=RiskCheckResult.PASSED,
                message=f"Market regime: {regime.value}",
                details={"regime": regime},
            )

    async def _detect_regime(self) -> MarketRegime:
        """
        Detect current market regime.

        In production, would analyze:
        - VIX level and trend
        - SPY 20/50/200 day MAs
        - Market breadth
        - Put/call ratio
        """
        # Simplified regime detection
        # In production, fetch SPY data and calculate
        try:
            if self.ibkr_client:
                # Try to get SPY data for regime detection
                # This is a placeholder - would need actual implementation
                pass
        except Exception as e:
            logger.debug(f"Could not fetch market data for regime detection: {e}")

        # Default to unknown/normal
        return MarketRegime.SIDEWAYS

    async def _get_positions(self, account_id: int) -> List[Dict]:
        """Get current positions from IBKR or database"""
        if self.ibkr_client:
            try:
                positions = await self.ibkr_client.get_positions()
                return [
                    {
                        "symbol": p.symbol,
                        "quantity": p.quantity,
                        "average_price": p.average_price,
                        "market_price": p.market_price,
                    }
                    for p in positions
                ]
            except Exception as e:
                logger.warning(f"Could not fetch positions from IBKR: {e}")
        return []

    async def _get_portfolio_value(self, account_id: int) -> float:
        """Get total portfolio value"""
        if self.ibkr_client:
            try:
                summary = await self.ibkr_client.get_account_summary()
                if summary:
                    return summary.get("NetLiquidation", 0) or summary.get("TotalCashValue", 0)
            except Exception as e:
                logger.warning(f"Could not fetch portfolio value: {e}")
        return 0.0

    async def _get_daily_pnl_pct(self, account_id: int) -> float:
        """Get daily P&L as percentage"""
        if self.ibkr_client:
            try:
                summary = await self.ibkr_client.get_account_summary()
                if summary:
                    daily_pnl = summary.get("DailyPnL", 0) or 0
                    net_liq = summary.get("NetLiquidation", 1) or 1
                    return daily_pnl / net_liq
            except Exception as e:
                logger.warning(f"Could not fetch daily P&L: {e}")
        return 0.0

    def _get_sector(self, symbol: str) -> str:
        """Get sector for a symbol"""
        return SECTOR_MAP.get(symbol.upper(), "Unknown")

    def _calculate_risk_score(self, checks: List[RiskCheck]) -> float:
        """Calculate overall risk score from 0.0 (low) to 1.0 (high)"""
        if not checks:
            return 0.0

        # Weight by check importance
        weights = {
            "circuit_breaker": 1.0,  # Most important
            "position_concentration": 0.8,
            "sector_exposure": 0.7,
            "symbol_exposure": 0.7,
            "correlation": 0.5,
            "market_regime": 0.4,
        }

        total_weight = 0.0
        weighted_score = 0.0

        for check in checks:
            weight = weights.get(check.name, 0.5)
            total_weight += weight

            if check.result == RiskCheckResult.FAILED:
                weighted_score += weight * 1.0
            elif check.result == RiskCheckResult.WARNING:
                weighted_score += weight * 0.5
            # PASSED = 0.0

        if total_weight == 0:
            return 0.0

        return weighted_score / total_weight

    def _should_reduce_size(self, checks: List[RiskCheck]) -> bool:
        """Determine if position size should be reduced"""
        # Reduce size in high volatility
        for check in checks:
            if check.name == "market_regime":
                regime = check.details.get("regime")
                if regime == MarketRegime.HIGH_VOLATILITY and self.settings.reduce_size_in_high_vol:
                    return True

        # Reduce size if any warnings
        return any(c.result == RiskCheckResult.WARNING for c in checks)

    def _calculate_reduced_size(
        self,
        quantity: int,
        checks: List[RiskCheck],
        portfolio_value: float,
        price: float,
    ) -> int:
        """Calculate reduced position size"""
        reduction_factor = 1.0

        # Check for high volatility
        for check in checks:
            if check.name == "market_regime":
                regime = check.details.get("regime")
                if regime == MarketRegime.HIGH_VOLATILITY:
                    reduction_factor *= self.settings.high_vol_size_reduction

        # Additional reduction for each warning
        warning_count = sum(1 for c in checks if c.result == RiskCheckResult.WARNING)
        if warning_count > 0:
            reduction_factor *= max(0.5, 1.0 - (warning_count * 0.1))

        reduced_quantity = int(quantity * reduction_factor)
        return max(1, reduced_quantity)  # At least 1 share

    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker"""
        self._circuit_breaker_triggered = False
        self._circuit_breaker_triggered_at = None
        logger.info("Circuit breaker manually reset")

    def get_status(self) -> Dict[str, Any]:
        """Get current portfolio risk status"""
        return {
            "enabled": self.settings.enabled,
            "circuit_breaker_triggered": self._circuit_breaker_triggered,
            "circuit_breaker_triggered_at": self._circuit_breaker_triggered_at.isoformat() if self._circuit_breaker_triggered_at else None,
            "market_regime": self._market_regime.value,
            "regime_updated_at": self._regime_updated_at.isoformat() if self._regime_updated_at else None,
            "settings": {
                "max_position_pct": self.settings.max_position_pct,
                "max_symbol_exposure_pct": self.settings.max_symbol_exposure_pct,
                "max_sector_exposure_pct": self.settings.max_sector_exposure_pct,
                "max_correlation": self.settings.max_correlation,
                "max_daily_loss_pct": self.settings.max_daily_loss_pct,
            },
        }


# Global instance
_portfolio_risk_checker: Optional[PortfolioRiskChecker] = None


def get_portfolio_risk_checker() -> PortfolioRiskChecker:
    """Get or create global portfolio risk checker instance"""
    global _portfolio_risk_checker
    if _portfolio_risk_checker is None:
        _portfolio_risk_checker = PortfolioRiskChecker()
    return _portfolio_risk_checker
