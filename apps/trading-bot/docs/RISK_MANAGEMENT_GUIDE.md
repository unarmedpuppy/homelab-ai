# Risk Management System Guide

## Overview

The Risk Management system provides comprehensive cash account compliance, position sizing, and profit taking rules for accounts with balances under $25,000.

**Last Updated**: December 19, 2024  
**Status**: Production Ready

---

## Features

### 1. Account Monitoring
- Automatic balance detection from IBKR
- Cash account mode activation (< $25k threshold)
- Balance caching for performance
- Thread-safe state management

### 2. Compliance Rules
- **PDT Prevention**: Tracks day trades in 5-day rolling window, blocks after 3
- **Settlement Tracking**: T+2 business day settlement period
- **Trade Frequency Limits**: Daily and weekly trade count limits
- **GFV Prevention**: Good Faith Violation detection (foundation in place)

### 3. Position Sizing
- Confidence-based sizing:
  - Low confidence (0.0-0.4): 1% of account
  - Medium confidence (0.4-0.7): 2.5% of account
  - High confidence (0.7-1.0): 4% of account
- Maximum position size cap: 10% of account
- Settled cash consideration for cash accounts

### 4. Profit Taking
- Three profit levels:
  - Level 1: 5% profit (exit 25%)
  - Level 2: 10% profit (exit 50%)
  - Level 3: 20% profit (exit remaining)
- Partial exit support
- Configurable thresholds

---

## API Usage

### Pre-Trade Validation

```python
POST /api/risk/validate-trade

{
    "account_id": 1,
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 10,  // Optional if confidence_score provided
    "price_per_share": 150.0,
    "confidence_score": 0.8,  // Optional
    "will_create_day_trade": false
}

Response:
{
    "is_valid": true,
    "can_proceed": true,
    "compliance_result": "allowed",
    "compliance_message": "All compliance checks passed",
    "position_size": {
        "size_usd": 800.0,
        "size_shares": 5,
        "confidence_level": "high",
        "base_percentage": 0.04,
        "actual_percentage": 0.04,
        "max_size_hit": false
    }
}
```

### Trade Execution

```python
POST /api/trading/execute

{
    "account_id": 1,
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 10,  // Optional - will use position sizing if confidence_score provided
    "price_per_share": 150.0,
    "confidence_score": 0.8,  // Optional - triggers automatic position sizing
    "strategy_id": 5,  // Optional
    "will_create_day_trade": false
}

Response:
{
    "status": "success",
    "trade_id": 123,
    "broker_order_id": 456,
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 5,  // May be adjusted by position sizing
    "price": 150.0,
    "validation": {
        "passed": true,
        "compliance_result": "allowed",
        "position_size": { ... }
    }
}
```

### Risk Status

```python
GET /api/risk/status?account_id=1

Response:
{
    "account_id": 1,
    "account_balance": 20000.0,
    "is_cash_account_mode": true,
    "threshold": 25000.0,
    "available_settled_cash": 18500.0,
    "compliance": {
        "day_trades_last_5_days": 1,
        "day_trade_limit": 3,
        "daily_trades": 2,
        "daily_limit": 5,
        "weekly_trades": 8,
        "weekly_limit": 20
    }
}
```

### Compliance Status

```python
GET /api/risk/compliance?account_id=1

Response:
{
    "account_id": 1,
    "cash_account_mode": true,
    "pdt": {
        "day_trades_count": 1,
        "limit": 3,
        "can_trade": true,
        "remaining_day_trades": 2
    },
    "trade_frequency": {
        "daily": {
            "count": 2,
            "limit": 5,
            "remaining": 3
        },
        "weekly": {
            "count": 8,
            "limit": 20,
            "remaining": 12
        }
    },
    "settlement": {
        "available_settled_cash": 18500.0,
        "settlement_period_days": 2
    }
}
```

---

## Configuration

All risk management settings are in `settings.py` under `RiskManagementSettings`:

```python
# Environment variables (RISK_ prefix)

RISK_CASH_ACCOUNT_THRESHOLD=25000.0  # Balance threshold for cash account mode
RISK_PDT_ENFORCEMENT_MODE=strict  # strict or warning
RISK_DAILY_TRADE_LIMIT=5  # Max trades per day
RISK_WEEKLY_TRADE_LIMIT=20  # Max trades per week

# Position sizing
RISK_POSITION_SIZE_LOW_CONFIDENCE=0.01  # 1%
RISK_POSITION_SIZE_MEDIUM_CONFIDENCE=0.025  # 2.5%
RISK_POSITION_SIZE_HIGH_CONFIDENCE=0.04  # 4%
RISK_MAX_POSITION_SIZE_PCT=0.10  # 10% hard cap

# Profit taking
RISK_PROFIT_TAKE_LEVEL_1=0.05  # 5%
RISK_PROFIT_TAKE_LEVEL_2=0.10  # 10%
RISK_PROFIT_TAKE_LEVEL_3=0.20  # 20%
RISK_PARTIAL_EXIT_ENABLED=true
RISK_PARTIAL_EXIT_LEVEL_1_PCT=0.25  # 25%
RISK_PARTIAL_EXIT_LEVEL_2_PCT=0.50  # 50%

# Settlement
RISK_SETTLEMENT_DAYS=2  # T+2
```

---

## Code Examples

### Using RiskManager Directly

```python
from src.core.risk import get_risk_manager

risk_mgr = get_risk_manager()

# Validate trade
validation = await risk_mgr.validate_trade(
    account_id=1,
    symbol="AAPL",
    side="BUY",
    quantity=10,
    price_per_share=150.0,
    confidence_score=0.8
)

if validation.can_proceed:
    # Execute trade
    pass
else:
    print(f"Trade blocked: {validation.compliance_check.message}")

# Get risk status
status = await risk_mgr.get_risk_status(account_id=1)
print(f"Cash account mode: {status.is_cash_account_mode}")
print(f"Day trades: {status.day_trade_count}/3")
```

### Position Sizing

```python
from src.core.risk import PositionSizingManager

sizing = PositionSizingManager()

# Calculate position size
result = await sizing.calculate_position_size(
    account_id=1,
    confidence_score=0.8,  # High confidence
    price_per_share=150.0
)

print(f"Position size: {result.size_shares} shares (${result.size_usd:,.2f})")
print(f"Confidence level: {result.confidence_level.value}")
```

### Profit Taking

```python
from src.core.risk import ProfitTakingManager

profit_mgr = ProfitTakingManager()

# Create exit plan
exit_plan = profit_mgr.create_exit_plan(
    entry_price=100.0,
    quantity=100
)

# Check profit levels
result = profit_mgr.check_profit_levels(
    current_price=105.0,  # 5% profit
    exit_plan=exit_plan,
    current_quantity=100
)

if result.should_exit:
    print(f"Exit {result.exit_quantity} shares at {result.profit_level.value}")
    print(f"Remaining: {result.remaining_shares} shares")
```

---

## Database Models

### CashAccountState
Tracks account balance and cash account mode status.

### DayTrade
Records day trades for PDT compliance.

### SettlementTracking
Tracks T+2 settlement periods for trades.

### TradeFrequencyTracking
Tracks daily and weekly trade counts.

---

## Integration Points

### Trade Execution
The `/api/trading/execute` endpoint automatically:
1. Validates trade with risk management
2. Calculates position size if confidence score provided
3. Records settlement tracking
4. Detects and records day trades
5. Increments trade frequency counters

### Strategy Integration
Strategies can:
- Provide confidence scores in TradingSignal
- Use position sizing via RiskManager
- Integrate profit taking in exit logic

---

## Testing

Run the comprehensive test suite:

```bash
python scripts/test_risk_management_e2e.py
```

Individual component tests:
- `scripts/test_account_monitor.py`
- `scripts/test_compliance.py`
- (Position sizing and profit taking tests to be added)

---

## Architecture

```
RiskManager (Unified Interface)
├── AccountMonitor (Balance & Cash Account Mode)
├── ComplianceManager (PDT, Settlement, Frequency)
├── PositionSizingManager (Confidence-Based Sizing)
└── ProfitTakingManager (Profit Levels & Partial Exits)
```

All components are independently usable but work together through RiskManager.

---

## Notes

- **Thread Safety**: AccountMonitor cache uses locks for thread safety
- **Database Sessions**: All database operations use proper session management
- **Error Handling**: Graceful degradation when components unavailable
- **Caching**: Balance cached for 5 minutes to reduce IBKR API calls
- **Settlement**: Weekend-aware T+2 calculation (holidays not yet supported)

---

## Future Enhancements

- Holiday calendar support for settlement calculations
- Enhanced GFV prevention logic
- Strategy-specific position sizing overrides
- Historical compliance reporting
- Risk limit configuration per account

