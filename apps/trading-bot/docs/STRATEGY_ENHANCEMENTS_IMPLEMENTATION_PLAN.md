# Strategy System Enhancements - Implementation Plan

## Overview

Enhance the Strategy System by implementing additional strategy types and optimization capabilities. This will expand the trading bot's strategy repertoire with proven trading patterns.

## Current Status

**Completed**:
- ✅ Base Strategy Framework
- ✅ Strategy Registry
- ✅ SMA Strategy
- ✅ Range Bound Strategy
- ✅ Level-Based Strategy
- ✅ Strategy Evaluation Engine
- ✅ Confluence & Sentiment Integration

**Planned Enhancements**:
- ⏳ Momentum Strategy
- ⏳ Mean Reversion Strategy
- ⏳ Breakout Strategy
- ⏳ Multi-Timeframe Strategy
- ⏳ Strategy Optimization Engine
- ⏳ Strategy Templates

## Implementation Plan

### Phase 1: Additional Strategy Types

#### 1.1 Momentum Strategy

**Purpose**: Identify and trade strong price momentum trends

**Implementation**:
- File: `src/core/strategy/momentum.py`
- Class: `MomentumStrategy(BaseStrategy)`
- Indicators: RSI, MACD, Price Rate of Change (ROC), Volume
- Entry Signals:
  - Strong uptrend: RSI > 70, MACD bullish crossover, increasing volume
  - Strong downtrend: RSI < 30, MACD bearish crossover, increasing volume
- Exit Signals:
  - Momentum exhaustion (RSI divergence)
  - Trend reversal (MACD crossover opposite direction)
  - Stop loss / take profit

**Configuration**:
```python
{
    "strategy": "momentum",
    "symbol": "AAPL",
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "roc_period": 10,
    "min_volume_increase": 1.2,  # 20% volume increase
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.05
}
```

#### 1.2 Mean Reversion Strategy

**Purpose**: Trade price reversions to mean after extreme moves

**Implementation**:
- File: `src/core/strategy/mean_reversion.py`
- Class: `MeanReversionStrategy(BaseStrategy)`
- Indicators: Bollinger Bands, RSI, Z-Score, Volume
- Entry Signals:
  - Oversold: Price touches lower Bollinger Band, RSI < 30, Z-score < -2
  - Overbought: Price touches upper Bollinger Band, RSI > 70, Z-score > 2
- Exit Signals:
  - Price returns to middle band (mean)
  - Stop loss if trend continues
  - Take profit at opposite band

**Configuration**:
```python
{
    "strategy": "mean_reversion",
    "symbol": "AAPL",
    "bb_period": 20,
    "bb_std": 2.0,
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "z_score_threshold": 2.0,
    "stop_loss_pct": 0.03,
    "take_profit_pct": 0.02
}
```

#### 1.3 Breakout Strategy

**Purpose**: Trade breakouts from consolidation ranges

**Implementation**:
- File: `src/core/strategy/breakout.py`
- Class: `BreakoutStrategy(BaseStrategy)`
- Indicators: Support/Resistance levels, Volume, ATR (Average True Range)
- Entry Signals:
  - Price breaks above resistance with increased volume (> 1.5x average)
  - Price breaks below support with increased volume
  - ATR confirms breakout strength
- Exit Signals:
  - Target: Previous resistance (now support) or support (now resistance)
  - Stop loss: Inside the broken range

**Configuration**:
```python
{
    "strategy": "breakout",
    "symbol": "AAPL",
    "range_detection_period": 20,  # Days to identify range
    "min_range_duration": 5,  # Minimum days in range
    "volume_threshold": 1.5,  # Volume multiplier
    "atr_period": 14,
    "atr_multiplier": 1.5,  # Minimum ATR for confirmation
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04
}
```

#### 1.4 Multi-Timeframe Strategy

**Purpose**: Confirm signals using multiple timeframes for higher confidence

**Implementation**:
- File: `src/core/strategy/multi_timeframe.py`
- Class: `MultiTimeframeStrategy(BaseStrategy)`
- Concept: Wrapper strategy that validates signals across timeframes
- Entry Logic:
  - Primary timeframe generates signal
  - Higher timeframe confirms trend direction
  - Lower timeframe provides entry timing
- Example: 5m signal confirmed by 15m trend and 1m entry

**Configuration**:
```python
{
    "strategy": "multi_timeframe",
    "symbol": "AAPL",
    "primary_timeframe": "5m",
    "trend_timeframe": "15m",
    "entry_timeframe": "1m",
    "base_strategy": "momentum",  # Strategy to use
    "trend_confirmation_required": True,
    "min_timeframe_agreement": 2  # At least 2 timeframes must agree
}
```

### Phase 2: Strategy Optimization Engine

#### 2.1 Parameter Optimization

**Purpose**: Automatically find optimal strategy parameters using historical data

**Implementation**:
- File: `src/core/strategy/optimization.py`
- Class: `StrategyOptimizer`
- Methods:
  - Grid search for parameter combinations
  - Genetic algorithm for parameter tuning
  - Walk-forward optimization
  - Monte Carlo parameter validation

**Features**:
- Define parameter ranges
- Run backtests for each combination
- Rank by performance metrics (Sharpe, win rate, etc.)
- Return optimal parameters

**Configuration**:
```python
{
    "strategy": "momentum",
    "optimization_type": "grid_search",
    "parameters": {
        "rsi_period": [10, 14, 20],
        "rsi_overbought": [65, 70, 75],
        "rsi_oversold": [25, 30, 35],
        "stop_loss_pct": [0.01, 0.02, 0.03],
        "take_profit_pct": [0.03, 0.05, 0.07]
    },
    "metric": "sharpe_ratio",
    "max_combinations": 1000
}
```

### Phase 3: Strategy Templates

#### 3.1 Pre-built Strategy Templates

**Purpose**: Provide ready-to-use strategy configurations

**Implementation**:
- File: `src/core/strategy/templates.py`
- Pre-configured strategy setups:
  - Conservative Momentum
  - Aggressive Momentum
  - Day Trading Mean Reversion
  - Swing Trading Breakout
  - Scalping Strategy

**Usage**:
```python
from src.core.strategy.templates import get_template

config = get_template("conservative_momentum", symbol="AAPL")
strategy = StrategyRegistry.get_strategy("momentum", config)
```

## File Structure

```
src/core/strategy/
├── __init__.py              # Exports
├── base.py                  # BaseStrategy (existing)
├── level_based.py           # LevelBasedStrategy (existing)
├── levels.py                # Level detection (existing)
├── registry.py              # Strategy registry (existing)
├── momentum.py              # NEW: MomentumStrategy
├── mean_reversion.py        # NEW: MeanReversionStrategy
├── breakout.py              # NEW: BreakoutStrategy
├── multi_timeframe.py       # NEW: MultiTimeframeStrategy
├── optimization.py          # NEW: StrategyOptimizer
└── templates.py             # NEW: Strategy templates
```

## Integration Points

### Strategy Registry

All new strategies must:
1. Inherit from `BaseStrategy`
2. Implement `generate_signal()` method
3. Register with `StrategyRegistry`
4. Follow existing configuration patterns

### Strategy Evaluator

Strategies integrate automatically via:
- `StrategyEvaluator.evaluate_strategy()`
- Signal callbacks for WebSocket broadcasting
- Sentiment and confluence filtering

### API Routes

Add strategy endpoints in `src/api/routes/strategies.py`:
- `POST /api/strategies/momentum` - Create momentum strategy
- `POST /api/strategies/mean-reversion` - Create mean reversion strategy
- `POST /api/strategies/breakout` - Create breakout strategy
- `POST /api/strategies/optimize` - Optimize strategy parameters
- `GET /api/strategies/templates` - List available templates

## Testing Strategy

1. **Unit Tests**: Test each strategy's signal generation logic
2. **Backtest Validation**: Verify strategies work with backtesting engine
3. **Integration Tests**: Test strategy registration and evaluation
4. **Parameter Optimization Tests**: Validate optimization engine

## Success Criteria

- [ ] All 4 new strategy types implemented and tested
- [ ] Strategies register correctly and appear in strategy list
- [ ] Strategies integrate with sentiment and confluence filtering
- [ ] Parameter optimization engine functional
- [ ] Strategy templates available via API
- [ ] Documentation complete for each strategy type
- [ ] Test scripts for each strategy

## Estimated Time

- **Phase 1** (Strategy Types): 20-25 hours
  - Momentum: 5-6 hours
  - Mean Reversion: 5-6 hours
  - Breakout: 5-6 hours
  - Multi-Timeframe: 5-7 hours

- **Phase 2** (Optimization): 15-20 hours

- **Phase 3** (Templates): 3-5 hours

**Total**: 38-50 hours

