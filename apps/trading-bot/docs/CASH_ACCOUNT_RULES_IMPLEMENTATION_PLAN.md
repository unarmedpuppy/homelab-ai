# Cash Account Rules & Risk Management - Implementation Plan

**Status**: 🔄 In Progress  
**Started**: December 19, 2024  
**Agent**: Auto  
**Priority**: High - Critical for Phase 1: Core Trading Foundation

---

## Overview

Implement comprehensive cash account rules and risk management features to ensure compliance with regulatory requirements and protect traders with accounts under $25k. This includes account balance detection, PDT avoidance, settlement period handling, trade frequency limits, GFV prevention, confidence-based position sizing, and aggressive profit taking rules.

**Goal**: Enable safe, compliant trading for accounts under $25k balance while implementing sophisticated risk management and position sizing.

---

## Requirements Analysis

### Cash Account Rules (Under $25k Balance)

1. **Account Balance Detection**
   - Detect when account balance < $25k
   - Automatic detection via IBKR account summary
   - Configurable threshold (default: $25,000)
   - Periodic checks and state management

2. **Cash Account Mode**
   - Enable/disable cash account restrictions
   - State persistence in database
   - Configuration-driven rules

3. **Pattern Day Trader (PDT) Avoidance**
   - Track day trades (same-day buy/sell)
   - Prevent PDT violations (max 3 day trades in 5 days)
   - Block trades that would trigger PDT status
   - Configurable: strict mode vs. warning mode

4. **Settlement Period Handling (T+2)**
   - Track trade execution dates
   - Calculate settlement dates (trade date + 2 business days)
   - Prevent using unsettled funds for new trades
   - Track available settled cash vs. total cash

5. **Trade Frequency Limits**
   - Configurable daily trade limits (default: 3-5 trades/day)
   - Weekly trade limits
   - Prevent excessive trading in cash accounts
   - Reset tracking at appropriate intervals

6. **Good Faith Violation (GFV) Prevention**
   - Detect and prevent GFV violations
   - GFV occurs when buying with unsettled funds and selling before settlement
   - Track settlement status of all funds
   - Block trades that would cause GFV

### Position Sizing by Confidence

1. **Confidence-Based Sizing**
   - Calculate position size based on signal confidence
   - Low confidence: 1% of account value (default)
   - Medium confidence: 2-3% of account value (default)
   - High confidence: Up to 4% of account value (default)
   - Configurable percentages per confidence level

2. **Strategy-Based Sizing**
   - Allow strategy module to override defaults
   - Strategy-specific sizing rules
   - Maximum position size hard cap
   - Respect cash account limitations

### Profit Taking Rules

1. **Aggressive Profit Taking**
   - Default: Take profits at 5-20% gains
   - Configurable profit thresholds
   - Strategy-driven exit logic (strategy controls exact thresholds)
   - Multiple exit levels supported

2. **Partial Exit Strategy**
   - Scale out positions (e.g., 25% at 5%, 50% at 10%, full at 20%)
   - Configurable scaling percentages and thresholds
   - Support for multiple partial exits

---

## Architecture Design

### Core Components

1. **Account Monitor Service** (`src/core/risk/account_monitor.py`)
   - Monitor account balance and status
   - Detect cash account mode activation
   - Track account value changes
   - Integration with IBKR account summary

2. **Cash Account Compliance Manager** (`src/core/risk/compliance.py`)
   - PDT tracking and prevention
   - Settlement period tracking (T+2)
   - Trade frequency limits
   - GFV prevention
   - Rule enforcement engine

3. **Position Sizing Manager** (`src/core/risk/position_sizing.py`)
   - Confidence-based position sizing
   - Strategy-based sizing overrides
   - Maximum position size enforcement
   - Cash availability checks

4. **Profit Taking Manager** (`src/core/risk/profit_taking.py`)
   - Aggressive profit taking logic
   - Partial exit strategies
   - Strategy-driven exit coordination
   - Exit level tracking

5. **Risk Management Integration** (`src/core/risk/manager.py`)
   - Unified risk management interface
   - Coordination between all risk components
   - Pre-trade validation
   - Risk rule enforcement

### Database Schema Extensions

**New Tables**:
- `cash_account_state` - Track cash account mode and balance history
- `day_trades` - Track day trades for PDT compliance
- `settlement_tracking` - Track trade settlements (T+2)
- `trade_frequency_tracking` - Track daily/weekly trade counts
- `position_sizing_rules` - Store position sizing configuration
- `profit_taking_rules` - Store profit taking configuration

**Enhanced Models**:
- `Account` - Add cash account mode flag, balance tracking
- `Trade` - Add settlement_date, day_trade_flag, confidence_score
- `Position` - Add confidence_score, sizing_method

### Configuration

**New Settings** (`src/config/settings.py`):
- Cash account threshold ($25k default)
- PDT enforcement mode (strict/warning)
- Trade frequency limits (daily/weekly)
- Confidence-based sizing percentages
- Profit taking thresholds
- Settlement period (T+2 default)

---

## Implementation Phases

### Phase 1: Foundation & Account Monitoring (Week 1)

**Goal**: Basic account balance detection and cash account mode activation

**Tasks**:
1. ✅ Create database models for cash account state
2. ✅ Create AccountMonitor service
3. ✅ Integrate with IBKR account summary
4. ✅ Implement balance detection logic
5. ✅ Add cash account mode state management
6. ✅ Create configuration settings
7. ✅ Add database migrations
8. ✅ Create test script

**Deliverables**:
- `src/core/risk/account_monitor.py`
- `src/data/database/models.py` (updates)
- `migrations/versions/XXX_add_cash_account_models.py`
- `scripts/test_account_monitor.py`

### Phase 2: Compliance Rules - PDT & Settlement (Week 1-2)

**Goal**: Implement PDT avoidance and T+2 settlement tracking

**Tasks**:
1. ✅ Create ComplianceManager service
2. ✅ Implement day trade tracking
3. ✅ Implement PDT violation prevention
4. ✅ Implement T+2 settlement tracking
5. ✅ Add trade settlement date calculation
6. ✅ Create settlement tracking database model
7. ✅ Integrate with trade execution
8. ✅ Add compliance checks to pre-trade validation
9. ✅ Create test script

**Deliverables**:
- `src/core/risk/compliance.py`
- Database models for settlement tracking and day trades
- Migration scripts
- `scripts/test_compliance.py`

### Phase 3: Trade Frequency & GFV Prevention (Week 2)

**Goal**: Implement trade frequency limits and GFV prevention

**Tasks**:
1. ✅ Implement trade frequency tracking (daily/weekly)
2. ✅ Add frequency limit enforcement
3. ✅ Implement GFV detection logic
4. ✅ Create GFV prevention checks
5. ✅ Add trade frequency database model
6. ✅ Integrate with trade execution flow
7. ✅ Add configuration for limits
8. ✅ Create test script

**Deliverables**:
- Updates to `src/core/risk/compliance.py`
- Database models for trade frequency tracking
- Migration scripts
- `scripts/test_trade_frequency.py`

### Phase 4: Confidence-Based Position Sizing (Week 2-3)

**Goal**: Implement confidence-based position sizing system

**Tasks**:
1. ✅ Create PositionSizingManager service
2. ✅ Implement confidence-based sizing logic
3. ✅ Add strategy-based sizing override support
4. ✅ Implement maximum position size enforcement
5. ✅ Add cash availability checks
6. ✅ Integrate with BaseStrategy.calculate_position_size()
7. ✅ Update strategy evaluation flow
8. ✅ Create configuration for sizing rules
9. ✅ Create test script

**Deliverables**:
- `src/core/risk/position_sizing.py`
- Updates to `src/core/strategy/base.py`
- Database models for position sizing rules
- Migration scripts
- `scripts/test_position_sizing.py`

### Phase 5: Profit Taking Rules (Week 3)

**Goal**: Implement aggressive profit taking and partial exits

**Tasks**:
1. ✅ Create ProfitTakingManager service
2. ✅ Implement aggressive profit taking logic (5-20% range)
3. ✅ Implement partial exit strategy support
4. ✅ Add strategy-driven exit coordination
5. ✅ Integrate with position exit logic
6. ✅ Add exit level tracking
7. ✅ Create configuration for profit taking rules
8. ✅ Update strategy exit methods
9. ✅ Create test script

**Deliverables**:
- `src/core/risk/profit_taking.py`
- Updates to `src/core/strategy/base.py`
- Database models for profit taking rules
- Migration scripts
- `scripts/test_profit_taking.py`

### Phase 6: Integration & Risk Manager (Week 3-4)

**Goal**: Unified risk management interface and integration

**Tasks**:
1. ✅ Create RiskManager unified interface
2. ✅ Integrate all risk components
3. ✅ Add pre-trade validation endpoint
4. ✅ Integrate with trade execution flow
5. ✅ Add risk rule enforcement to API routes
6. ✅ Create comprehensive test suite
7. ✅ Add API endpoints for risk status
8. ✅ Documentation updates

**Deliverables**:
- `src/core/risk/manager.py`
- Updates to `src/api/routes/trading.py`
- New API routes for risk management
- Integration tests
- Documentation updates

### Phase 7: Testing & Refinement (Week 4)

**Goal**: Comprehensive testing and refinement

**Tasks**:
1. ✅ End-to-end testing of all cash account rules
2. ✅ Test PDT scenarios
3. ✅ Test settlement period handling
4. ✅ Test position sizing with various confidence levels
5. ✅ Test profit taking scenarios
6. ✅ Performance testing
7. ✅ Edge case testing
8. ✅ Documentation completion
9. ✅ Code review and refinement

**Deliverables**:
- Comprehensive test suite
- Test results documentation
- Updated documentation
- Performance benchmarks

---

## Technical Design Decisions

### 1. Account Balance Detection

**Approach**: Periodic polling of IBKR account summary with caching
- Poll every 5 minutes (configurable)
- Cache balance to reduce API calls
- Update cache on trade execution
- Store balance history in database

**Implementation**:
```python
class AccountMonitor:
    async def check_account_balance(self) -> AccountStatus
    async def is_cash_account_mode(self) -> bool
    async def get_available_cash(self) -> float
```

### 2. PDT Tracking

**Approach**: Track all trades, identify day trades, count in rolling 5-day window
- Store all trades with execution timestamp
- Day trade = buy and sell same symbol on same day
- Count day trades in last 5 business days
- Block if count >= 3

**Implementation**:
```python
class ComplianceManager:
    def check_pdt_compliance(self, symbol: str, side: OrderSide) -> ComplianceResult
    def record_day_trade(self, symbol: str, buy_date: date, sell_date: date)
    def get_day_trade_count(self, lookback_days: int = 5) -> int
```

### 3. Settlement Tracking

**Approach**: Calculate settlement dates for all trades, track available settled cash
- Settlement date = trade date + 2 business days
- Track available settled cash vs. total cash
- Block trades if insufficient settled cash

**Implementation**:
```python
def calculate_settlement_date(trade_date: date) -> date
def get_available_settled_cash() -> float
def check_settled_cash_available(required_amount: float) -> bool
```

### 4. Position Sizing

**Approach**: Confidence score mapped to account percentage, with strategy overrides
- Confidence ranges: Low (0.0-0.4), Medium (0.4-0.7), High (0.7-1.0)
- Calculate position size = account_value * percentage_for_confidence
- Apply strategy override if provided (with limits)
- Enforce maximum position size cap

**Implementation**:
```python
class PositionSizingManager:
    def calculate_position_size(
        self, 
        confidence: float, 
        account_value: float,
        strategy_override: Optional[float] = None
    ) -> int
```

### 5. Profit Taking

**Approach**: Strategy-driven with configurable thresholds and partial exits
- Strategy controls exact exit logic and thresholds
- Support multiple exit levels (e.g., 5%, 10%, 20%)
- Partial exit support (e.g., 25% at 5%, 50% at 10%, full at 20%)
- Default aggressive thresholds if strategy doesn't specify

**Implementation**:
```python
class ProfitTakingManager:
    def check_profit_targets(self, position: Position, current_price: float) -> List[ExitSignal]
    def calculate_partial_exit(self, position: Position, target_pct: float) -> int
```

---

## Integration Points

### With Existing Systems

1. **IBKR Client Integration**
   - Use `IBKRClient.get_account_summary()` for balance
   - Use `IBKRClient.place_order()` - add pre-order validation
   - Track trades in compliance system

2. **Strategy System Integration**
   - Extend `BaseStrategy.calculate_position_size()` to use PositionSizingManager
   - Add confidence score to `TradingSignal`
   - Integrate profit taking with `should_exit()`

3. **Trade Execution Integration**
   - Add pre-trade validation in `src/api/routes/trading.py`
   - Check compliance before order placement
   - Record trades in compliance tracking

4. **Database Integration**
   - New models in `src/data/database/models.py`
   - Repository methods for cash account state, settlements, day trades
   - Migrations via Alembic

5. **Configuration Integration**
   - Add settings to `src/config/settings.py`
   - Environment variable support
   - Default values with override capability

---

## File Structure

```
src/
├── core/
│   └── risk/
│       ├── __init__.py
│       ├── manager.py              # Unified risk management interface
│       ├── account_monitor.py      # Account balance and mode detection
│       ├── compliance.py           # PDT, settlement, GFV, frequency limits
│       ├── position_sizing.py      # Confidence-based position sizing
│       └── profit_taking.py        # Profit taking rules and partial exits
├── data/
│   └── database/
│       └── models.py               # Extended with risk management models
├── config/
│   └── settings.py                 # Extended with risk management settings
├── api/
│   └── routes/
│       ├── trading.py              # Updated with risk validation
│       └── risk.py                 # New risk management endpoints
└── scripts/
    ├── test_account_monitor.py
    ├── test_compliance.py
    ├── test_trade_frequency.py
    ├── test_position_sizing.py
    └── test_profit_taking.py

migrations/
└── versions/
    ├── XXX_add_cash_account_models.py
    ├── XXX_add_settlement_tracking.py
    └── XXX_add_risk_management_models.py
```

---

## Testing Strategy

### Unit Tests

- Account balance detection
- PDT compliance checks
- Settlement date calculations
- Position sizing calculations
- Profit taking logic
- Trade frequency tracking
- GFV detection

### Integration Tests

- Account monitor with IBKR
- Compliance checks with trade execution
- Position sizing with strategy integration
- Profit taking with position exits
- End-to-end cash account workflow

### Test Scenarios

1. **Account Balance Detection**
   - Balance above $25k → no restrictions
   - Balance below $25k → cash account mode enabled
   - Balance transitions → state changes

2. **PDT Scenarios**
   - Day trade count < 3 → allowed
   - Day trade count = 3 → blocked
   - Rolling window → old trades drop off

3. **Settlement Scenarios**
   - T+2 calculation for trade dates
   - Weekends/holidays handling
   - Available settled cash tracking

4. **Position Sizing Scenarios**
   - Low confidence → 1% sizing
   - High confidence → 4% sizing
   - Strategy override with limits

5. **Profit Taking Scenarios**
   - 5% gain → partial exit (25%)
   - 10% gain → partial exit (50%)
   - 20% gain → full exit

---

## Configuration Reference

### Environment Variables

```bash
# Cash Account Rules
RISK_CASH_ACCOUNT_THRESHOLD=25000.0
RISK_PDT_ENFORCEMENT_MODE=strict  # strict or warning
RISK_DAILY_TRADE_LIMIT=5
RISK_WEEKLY_TRADE_LIMIT=20

# Position Sizing
RISK_POSITION_SIZE_LOW_CONFIDENCE=0.01    # 1%
RISK_POSITION_SIZE_MEDIUM_CONFIDENCE=0.025 # 2.5%
RISK_POSITION_SIZE_HIGH_CONFIDENCE=0.04    # 4%
RISK_MAX_POSITION_SIZE_PCT=0.10           # 10% hard cap

# Profit Taking
RISK_PROFIT_TAKE_LEVEL_1=0.05   # 5%
RISK_PROFIT_TAKE_LEVEL_2=0.10   # 10%
RISK_PROFIT_TAKE_LEVEL_3=0.20   # 20%
RISK_PARTIAL_EXIT_ENABLED=true
```

---

## Success Criteria

1. ✅ Account balance automatically detected and cash account mode activated when < $25k
2. ✅ PDT violations prevented (max 3 day trades in 5 days)
3. ✅ T+2 settlement period correctly tracked and enforced
4. ✅ Trade frequency limits enforced (daily/weekly)
5. ✅ GFV violations prevented
6. ✅ Position sizing works based on confidence (1-4% of account)
7. ✅ Strategy can override position sizing (with limits)
8. ✅ Aggressive profit taking implemented (5-20% range)
9. ✅ Partial exit strategy supported
10. ✅ All rules configurable via settings
11. ✅ Comprehensive test coverage
12. ✅ Integration with existing trading system
13. ✅ Documentation complete

---

## Dependencies

- Existing IBKR client integration
- Database models and migrations
- Strategy base classes
- Trade execution flow
- Configuration management system

---

## Risks & Mitigations

1. **Risk**: Complex settlement date calculations (weekends, holidays)
   - **Mitigation**: Use business day calculations, test thoroughly

2. **Risk**: Performance impact of compliance checks
   - **Mitigation**: Cache results, batch checks, optimize database queries

3. **Risk**: Edge cases in PDT tracking
   - **Mitigation**: Comprehensive test scenarios, handle all edge cases

4. **Risk**: Integration complexity
   - **Mitigation**: Clear interfaces, incremental integration, thorough testing

---

## Next Steps

1. Review and approve implementation plan
2. Start Phase 1: Account Monitor implementation
3. Create database models and migrations
4. Implement account balance detection
5. Proceed through phases sequentially

---

**Last Updated**: December 19, 2024  
**Next Review**: After Phase 1 completion

