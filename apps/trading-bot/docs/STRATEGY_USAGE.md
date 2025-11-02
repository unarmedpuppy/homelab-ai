# Strategy System Usage Guide

## Quick Start

### Using the Range-Bound Strategy

```python
from src.core.strategies import RangeBoundStrategy

# Configure strategy
config = {
    "symbol": "SPY",
    "timeframe": "5m",
    "entry": {
        "levels": ["previous_day_high", "previous_day_low"],
        "proximity_threshold": 0.001  # 0.1%
    },
    "exit": {
        "stop_loss_pct": 0.005,  # 0.5%
        "take_profit_type": "opposite_level"
    }
}

# Create strategy
strategy = RangeBoundStrategy(config)

# Generate signal
signal = strategy.generate_signal(market_data)

if signal.signal_type.value == "BUY":
    print(f"Buy signal: ${signal.price:.2f}")
    print(f"Stop loss: ${signal.stop_loss:.2f}")
    print(f"Take profit: ${signal.take_profit:.2f}")
```

### Using the Evaluation Engine

```python
from src.core.evaluation import StrategyEvaluator

# Create evaluator
evaluator = StrategyEvaluator()

# Add strategy
config = {
    "symbol": "SPY",
    "timeframe": "5m",
    "entry": {"levels": ["previous_day_high", "previous_day_low"]},
    "exit": {"stop_loss_pct": 0.005}
}

evaluator.add_strategy('range_bound', config, enabled=True)

# Evaluate with market data
signal = evaluator.evaluate_strategy('range_bound_SPY', market_data)

# Check exit conditions
exit_signal = evaluator.check_exit_conditions('range_bound_SPY', market_data)
```

## API Endpoints

### List Available Strategies
```bash
GET /api/strategies
```

### Get Strategy Info
```bash
GET /api/strategies/range_bound
```

### Add Strategy to Evaluator
```bash
POST /api/strategies/add
{
    "strategy_type": "range_bound",
    "config": {
        "symbol": "SPY",
        "timeframe": "5m",
        "entry": {
            "levels": ["previous_day_high", "previous_day_low"],
            "proximity_threshold": 0.001
        },
        "exit": {
            "stop_loss_pct": 0.005,
            "take_profit_type": "opposite_level"
        }
    },
    "enabled": true
}
```

### List Active Strategies
```bash
GET /api/strategies/active
```

### Enable/Disable Strategy
```bash
POST /api/strategies/range_bound_SPY/enable
POST /api/strategies/range_bound_SPY/disable
```

### Get Evaluation Statistics
```bash
GET /api/strategies/stats
```

## Testing

### Test Range-Bound Strategy
```bash
python scripts/test_range_bound_strategy.py
```

### Test Evaluation Engine
```bash
python scripts/test_evaluation_engine.py
```

## Configuration Options

### Range-Bound Strategy

**Entry Configuration**:
- `levels`: List of levels to use (`["previous_day_high", "previous_day_low"]`)
- `proximity_threshold`: How close price must be to level (default: 0.001 = 0.1%)
- `volume_confirmation`: Require volume confirmation (default: false)
- `min_volume_multiple`: Minimum volume multiple for confirmation (default: 1.0)

**Exit Configuration**:
- `stop_loss_pct`: Stop loss percentage from entry (default: 0.005 = 0.5%)
- `take_profit_type`: Type of take profit (`"opposite_level"` or `"percentage"`)
- `take_profit_threshold`: Threshold for level-based take profit (default: 0.002 = 0.2%)

**Risk Management**:
- `max_position_size`: Maximum position size
- `risk_per_trade`: Risk per trade as percentage (default: 0.02 = 2%)
- `default_qty`: Default quantity if position sizing fails

## Next Steps

1. **Backtesting**: Integrate strategies with backtesting engine
2. **Live Trading**: Connect to IBKR for live execution
3. **More Strategies**: Implement breakout, mean reversion, etc.
4. **Multi-Timeframe**: Add multi-timeframe confirmation

