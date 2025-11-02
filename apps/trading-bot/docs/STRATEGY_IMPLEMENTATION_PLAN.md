# Strategy Implementation Plan

## Quick Summary

This plan outlines the modular approach to implementing trading strategies, starting with the SPY PDH/PDL range-bound strategy example.

## Strategy Example: SPY Range-Bound (PDH/PDL)

**Goal**: Trade SPY on 5-minute chart using Previous Day High (PDH) and Previous Day Low (PDL) as entry/exit levels.

**Logic**:
1. **Entry**: When price approaches PDH or PDL within 0.1%
2. **Stop Loss**: 0.5% from entry level
3. **Take Profit**: When price approaches opposite range (PDL if entered at PDH, vice versa)

## Implementation Roadmap

### ✅ Phase 1: Core Infrastructure (Priority: HIGH)

**Files to Create/Modify**:
- `src/core/strategy/base.py` - Enhance BaseStrategy
- `src/core/strategy/levels.py` - Price level detection
- `src/core/strategy/level_based.py` - Level-based strategy base class

**Key Features**:
- [x] PriceLevel data structure
- [ ] Previous Day High/Low detection
- [ ] Level proximity calculations
- [ ] Multi-timeframe data fetching support

### ✅ Phase 2: Range-Bound Strategy (Priority: HIGH)

**Files to Create**:
- `src/core/strategies/range_bound_strategy.py`

**Implementation Steps**:
1. Create `RangeBoundStrategy` class extending `LevelBasedStrategy`
2. Implement PDH/PDL level identification
3. Implement entry logic:
   - Check if price is within threshold of PDH or PDL
   - Verify volume confirmation (optional)
   - Check market hours (optional filter)
4. Implement exit logic:
   - Stop loss: Fixed percentage from entry
   - Take profit: Opposite level approach
5. Add position sizing based on risk management

**Configuration Example**:
```python
config = {
    "name": "SPY_PDH_PDL_Range",
    "symbol": "SPY",
    "timeframe": "5m",
    "entry": {
        "levels": ["previous_day_high", "previous_day_low"],
        "proximity_threshold": 0.001,  # 0.1%
        "volume_confirmation": True
    },
    "exit": {
        "stop_loss_pct": 0.005,  # 0.5%
        "take_profit_type": "opposite_level",
        "take_profit_threshold": 0.002  # 0.2%
    },
    "risk_management": {
        "max_position_size": 100,
        "risk_per_trade": 0.02
    }
}
```

### ✅ Phase 3: Strategy Registry & Factory (Priority: MEDIUM)

**Files to Create/Modify**:
- `src/core/strategy/registry.py`
- Update `src/core/strategy.py` StrategyFactory

**Features**:
- Auto-discovery of strategy classes
- Strategy metadata management
- Configuration validation
- Strategy instantiation

### ✅ Phase 4: Evaluation Engine (Priority: MEDIUM)

**Files to Create**:
- `src/core/evaluation/evaluator.py`

**Features**:
- Real-time strategy evaluation
- Signal generation
- Signal filtering and prioritization
- Integration with position management

### ✅ Phase 5: API Integration (Priority: MEDIUM)

**Files to Modify**:
- `src/api/routes/trading.py`

**New Endpoints**:
- `POST /api/strategies/evaluate` - Evaluate strategy
- `GET /api/strategies/{name}/signals/{symbol}` - Get signals
- `POST /api/strategies/{name}/enable` - Enable strategy
- `POST /api/strategies/{name}/disable` - Disable strategy

## Quick Start: Range-Bound Strategy Implementation

### Step 1: Create Level Detection

```python
# src/core/strategy/levels.py
class LevelDetector:
    def get_previous_day_levels(self, df: pd.DataFrame, 
                                timeframe: str) -> Dict[str, PriceLevel]:
        """Get Previous Day High and Low"""
        # Group by day, find high/low
        # Return PDH and PDL PriceLevel objects
        pass
```

### Step 2: Create Strategy Class

```python
# src/core/strategies/range_bound_strategy.py
class RangeBoundStrategy(LevelBasedStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.entry_threshold = config['entry']['proximity_threshold']
        self.stop_loss_pct = config['exit']['stop_loss_pct']
        
    def generate_signal(self, data: pd.DataFrame, 
                       position: Optional[Position] = None) -> TradingSignal:
        # 1. Get PDH and PDL
        levels = self.detect_levels(data)
        pdh = levels.get('previous_day_high')
        pdl = levels.get('previous_day_low')
        
        # 2. Check proximity to levels
        current_price = data['close'].iloc[-1]
        
        # 3. Generate entry signal if close enough
        if self._near_level(current_price, pdh, self.entry_threshold):
            return self._create_buy_signal(current_price, pdh, 'pdh')
        elif self._near_level(current_price, pdl, self.entry_threshold):
            return self._create_buy_signal(current_price, pdl, 'pdl')
        
        return self._create_hold_signal()
    
    def should_exit(self, position: Position, 
                   data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        # Check stop loss and take profit conditions
        pass
```

### Step 3: Test with Historical Data

```python
# Test script
from src.core.strategies.range_bound_strategy import RangeBoundStrategy

config = {
    "symbol": "SPY",
    "timeframe": "5m",
    "entry": {"proximity_threshold": 0.001},
    "exit": {"stop_loss_pct": 0.005}
}

strategy = RangeBoundStrategy(config)
# Load SPY 5-minute data
data = load_historical_data("SPY", "5m", "2024-01-01", "2024-01-31")
signal = strategy.generate_signal(data)
```

## Design Decisions

### 1. Modular Strategy Classes
- Each strategy is a separate class
- Inherits from base classes (BaseStrategy, LevelBasedStrategy)
- Self-contained logic

### 2. Configuration-Driven
- Strategies configured via dictionaries/YAML
- Easy to modify without code changes
- Supports strategy variants

### 3. Level-Based Abstraction
- Common pattern: trading around price levels
- Reusable level detection logic
- Extensible to support/resistance, pivots, etc.

### 4. Multi-Timeframe Support
- Strategies can analyze multiple timeframes
- Primary timeframe for signals
- Confirmation timeframes optional

## Testing Strategy

### Unit Tests
```python
def test_pdh_pdl_detection():
    # Test that PDH/PDL are correctly identified
    pass

def test_entry_near_pdh():
    # Test entry signal when price near PDH
    pass

def test_stop_loss_calculation():
    # Test stop loss from entry level
    pass

def test_take_profit_opposite_level():
    # Test exit at opposite level
    pass
```

### Backtesting
- Use historical SPY 5-minute data
- Validate signals are generated correctly
- Check entry/exit timing
- Calculate performance metrics

## Next Steps

1. **Immediate**: Implement LevelDetector with PDH/PDL detection
2. **Next**: Create RangeBoundStrategy class
3. **Then**: Add to StrategyRegistry
4. **Finally**: Integrate with evaluation engine

## Questions to Consider

1. **Timeframe Handling**: Should strategies handle data resampling or assume pre-aggregated data?
   - **Decision**: Strategies assume correctly formatted data; data provider handles aggregation

2. **Level Persistence**: How long should levels remain valid?
   - **Decision**: Levels recalculated each day; PDH/PDL reset daily

3. **Multiple Entries**: Allow multiple entries on same level?
   - **Decision**: Configurable; default: one position at a time

4. **Order Execution**: Market orders vs limit orders near levels?
   - **Decision**: Configurable per strategy; default: limit orders at level ± threshold

---

**Ready to start implementation?** Review the architecture document and provide feedback on the approach!

