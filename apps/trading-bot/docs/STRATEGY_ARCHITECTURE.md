# Trading Strategy Architecture

## Overview

This document outlines the modular architecture for implementing and managing trading strategies in the trading bot. The system is designed to support multiple strategy types, timeframes, and evaluation modes (live trading, backtesting, paper trading).

## Core Design Principles

1. **Modularity**: Each strategy is a self-contained module with clear entry/exit logic
2. **Composability**: Strategies can combine multiple indicators and conditions
3. **Testability**: All strategies can be backtested and unit tested
4. **Configurability**: Strategy parameters are externalized and easily adjustable
5. **Multi-timeframe**: Support for analyzing multiple timeframes simultaneously
6. **Level-based**: Support for trading around key price levels (support/resistance, previous day high/low)

## Architecture Components

### 1. Strategy Base Classes

#### `BaseStrategy` (Abstract)
- Core interface all strategies must implement
- Handles common functionality (position sizing, risk management)
- Provides access to technical indicators

**Key Methods**:
- `generate_signal(data, position) -> TradingSignal`
- `should_exit(position, data) -> Tuple[bool, ExitReason]`
- `evaluate_entry_conditions(data) -> Dict[str, Any]`
- `evaluate_exit_conditions(position, data) -> Dict[str, Any]`

#### `LevelBasedStrategy` (Abstract)
- Extends `BaseStrategy`
- Adds support for price levels (support/resistance, PDH/PDL)
- Handles level detection and proximity calculations

**Key Methods**:
- `identify_levels(data) -> List[PriceLevel]`
- `check_level_proximity(price, level, threshold) -> bool`
- `get_entry_levels(data) -> List[PriceLevel]`
- `get_exit_levels(data) -> List[PriceLevel]`

#### `MultiTimeframeStrategy` (Abstract)
- Extends `BaseStrategy`
- Supports analysis across multiple timeframes
- Aggregates signals from different timeframes

**Key Methods**:
- `get_data_for_timeframe(timeframe) -> pd.DataFrame`
- `evaluate_all_timeframes() -> Dict[str, TradingSignal]`
- `aggregate_signals(signals) -> TradingSignal`

### 2. Data Structures

#### `PriceLevel`
```python
@dataclass
class PriceLevel:
    price: float
    level_type: LevelType  # SUPPORT, RESISTANCE, PDH, PDL, PIVOT
    strength: float  # 0.0 to 1.0
    timeframe: str  # "5m", "1h", "1d"
    timestamp: datetime
    touches: int  # Number of times price touched this level
```

#### `TradingSignal` (Enhanced)
```python
@dataclass
class TradingSignal:
    signal_type: SignalType  # BUY, SELL, HOLD
    symbol: str
    price: float
    quantity: int
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]
    entry_level: Optional[PriceLevel]  # NEW: Related price level
    stop_loss: Optional[float]  # NEW: Calculated stop loss
    take_profit: Optional[float]  # NEW: Calculated take profit
    timeframe: str  # NEW: Primary timeframe for signal
```

#### `StrategyConfig`
```python
@dataclass
class StrategyConfig:
    name: str
    strategy_type: str
    symbol: str
    timeframes: List[str]  # ["5m", "15m", "1h"]
    entry_conditions: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    risk_management: Dict[str, Any]
    position_sizing: Dict[str, Any]
    filters: Dict[str, Any]  # Additional filters (volume, volatility, etc.)
```

### 3. Level Detection System

#### `LevelDetector`
Utility class for identifying price levels:

- **Previous Day High/Low**: Highest/lowest price from previous trading day
- **Support/Resistance**: Areas where price reversed multiple times
- **Pivot Points**: Standard pivot point calculations (PP, R1, R2, S1, S2)
- **Fibonacci Levels**: Fibonacci retracement/extension levels
- **Volume Profile**: Price levels with high volume concentration

**Methods**:
- `get_previous_day_levels(data, timeframe) -> Dict[str, PriceLevel]`
- `detect_support_resistance(data, lookback) -> List[PriceLevel]`
- `calculate_pivot_points(data) -> Dict[str, PriceLevel]`

### 4. Strategy Examples

#### Range-Bound Strategy (PDH/PDL)
The example strategy you described:

**Configuration**:
```python
{
    "name": "PDH_PDL_Range_Strategy",
    "symbol": "SPY",
    "timeframes": ["5m"],
    "entry_conditions": {
        "type": "level_proximity",
        "levels": ["previous_day_high", "previous_day_low"],
        "proximity_threshold": 0.001,  # 0.1% within level
        "volume_confirmation": True,
        "min_volume_multiple": 1.2
    },
    "exit_conditions": {
        "take_profit": {
            "type": "opposite_level",
            "from_entry": "previous_day_high",  # If entered at PDL, exit at PDH
            "proximity_threshold": 0.002
        },
        "stop_loss": {
            "type": "percentage",
            "percentage": 0.005,  # 0.5%
            "from_level": True  # From entry level
        }
    },
    "risk_management": {
        "max_position_size": 100,
        "risk_per_trade": 0.02
    }
}
```

**Logic**:
1. Identify Previous Day High (PDH) and Previous Day Low (PDL)
2. Watch 5-minute chart
3. Enter when price approaches PDH or PDL within threshold
4. Stop loss: Small percentage from entry level
5. Take profit: When price approaches opposite range (PDL if entered at PDH, vice versa)

### 5. Strategy Registry

#### `StrategyRegistry`
Central registry for all available strategies:

- Auto-discovers strategy classes
- Provides strategy metadata
- Handles strategy instantiation
- Manages strategy dependencies

**Methods**:
- `register_strategy(strategy_class, name, config_schema)`
- `get_strategy(name, config) -> BaseStrategy`
- `list_strategies() -> List[str]`
- `get_strategy_info(name) -> Dict[str, Any]`

### 6. Strategy Evaluator

#### `StrategyEvaluator`
Real-time strategy evaluation engine:

- Evaluates strategies against current market data
- Manages multiple active strategies
- Handles signal generation and filtering
- Integrates with position management

**Key Methods**:
- `evaluate_strategy(strategy, symbol) -> TradingSignal`
- `evaluate_all_strategies(symbol) -> List[TradingSignal]`
- `should_execute_signal(signal, current_positions) -> bool`
- `update_strategy_state(strategy, market_data)`

## Implementation Plan

### Phase 1: Foundation (Week 1)
1. ✅ Enhance `BaseStrategy` with level-based methods
2. ✅ Create `PriceLevel` data structure
3. ✅ Implement `LevelDetector` utility
4. ✅ Add multi-timeframe data fetching

### Phase 2: Level Detection (Week 1)
1. Implement Previous Day High/Low detection
2. Implement Support/Resistance detection
3. Implement Pivot Point calculations
4. Add level strength calculation (touch count, volume)

### Phase 3: Range-Bound Strategy (Week 2)
1. Create `RangeBoundStrategy` class extending `LevelBasedStrategy`
2. Implement PDH/PDL entry logic
3. Implement opposite-level exit logic
4. Add stop loss calculation from entry level
5. Test with SPY 5-minute data

### Phase 4: Strategy System (Week 2)
1. Implement `StrategyRegistry`
2. Enhance `StrategyFactory` with registry integration
3. Create strategy configuration schema validation
4. Add strategy metadata system

### Phase 5: Evaluation Engine (Week 3)
1. Implement `StrategyEvaluator`
2. Add real-time market data integration
3. Create signal aggregation logic
4. Integrate with position management

### Phase 6: Additional Strategies (Ongoing)
1. Breakout Strategy
2. Mean Reversion Strategy
3. Momentum Strategy
4. Multi-timeframe Confirmation Strategy

## File Structure

```
src/
├── core/
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── base.py                    # BaseStrategy
│   │   ├── level_based.py            # LevelBasedStrategy
│   │   ├── multi_timeframe.py        # MultiTimeframeStrategy
│   │   ├── indicators.py             # TechnicalIndicators (enhanced)
│   │   ├── levels.py                 # PriceLevel, LevelDetector
│   │   └── registry.py               # StrategyRegistry
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── sma_strategy.py           # Existing SMA strategy
│   │   ├── range_bound_strategy.py   # PDH/PDL range strategy
│   │   ├── breakout_strategy.py      # Breakout strategy
│   │   └── mean_reversion_strategy.py # Mean reversion
│   └── evaluation/
│       ├── __init__.py
│       ├── evaluator.py              # StrategyEvaluator
│       └── signal_aggregator.py      # Signal aggregation logic
```

## Configuration Schema

### Strategy Configuration (JSON/YAML)
```yaml
strategies:
  - name: spy_pdh_pdl_range
    type: range_bound
    symbol: SPY
    enabled: true
    timeframes:
      primary: "5m"
      confirmation: []
    entry:
      type: level_proximity
      levels: [previous_day_high, previous_day_low]
      proximity_threshold: 0.001
      volume_confirmation: true
      min_volume_multiple: 1.2
      filters:
        - name: market_hours
          value: true
        - name: min_volume
          value: 5000000
    exit:
      take_profit:
        type: opposite_level
        proximity_threshold: 0.002
      stop_loss:
        type: percentage
        percentage: 0.005
        from_level: true
    risk_management:
      max_position_size: 100
      risk_per_trade: 0.02
      max_daily_trades: 10
```

## API Integration

### Strategy Management Endpoints
```
GET    /api/strategies                 # List all strategies
GET    /api/strategies/{name}          # Get strategy details
POST   /api/strategies/{name}/evaluate # Evaluate strategy for symbol
POST   /api/strategies/{name}/enable   # Enable strategy
POST   /api/strategies/{name}/disable  # Disable strategy
PUT    /api/strategies/{name}/config   # Update strategy config
```

### Real-time Evaluation
```
GET    /api/strategies/{name}/signals/{symbol}  # Get current signals
WS     /ws/strategies/{name}/signals            # WebSocket for live signals
```

## Testing Strategy

### Unit Tests
- Test level detection accuracy
- Test entry/exit conditions
- Test position sizing
- Test risk management

### Backtesting
- Historical data validation
- Performance metrics
- Walk-forward analysis
- Monte Carlo simulation

### Paper Trading
- Live data validation
- Execution simulation
- Performance tracking
- Risk monitoring

## Next Steps

1. Review and approve this architecture
2. Implement Phase 1 components
3. Create PDH/PDL range-bound strategy as first example
4. Test with historical SPY data
5. Integrate with existing trading bot infrastructure

---

**Questions or Feedback?**
Please review this architecture and provide feedback before implementation begins.

