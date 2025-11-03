# Trading Scheduler Implementation Plan

**Priority**: 🔴 HIGH - Critical for automatic trading  
**Status**: 🔄 In Progress  
**Start Date**: 2024-12-19

## Overview

Implement a background scheduler/loop that automatically:
1. Evaluates enabled strategies on configurable intervals
2. Fetches market data for active strategies
3. Generates trading signals
4. Executes trades when signals meet confidence and risk thresholds
5. Monitors exit conditions for existing positions
6. Manages lifecycle (start/stop/pause)

## Architecture

### Components

1. **TradingScheduler** (`src/core/scheduler/trading_scheduler.py`)
   - Main scheduler service
   - Manages evaluation loop
   - Coordinates strategy evaluation, signal generation, and trade execution
   - Handles position monitoring and exit checks

2. **Scheduler Settings** (`src/config/settings.py`)
   - Configurable intervals
   - Enable/disable scheduler
   - Execution thresholds

3. **API Integration** (`src/api/routes/scheduler.py`)
   - Start/stop/pause scheduler
   - Get scheduler status
   - Configuration management

4. **FastAPI Lifecycle** (`src/api/main.py`)
   - Start scheduler on app startup (if enabled)
   - Stop scheduler on app shutdown

## Implementation Steps

### Phase 1: Core Scheduler Service ✅
- [x] Create TradingScheduler class
- [x] Implement evaluation loop
- [x] Strategy evaluation integration
- [x] Market data fetching
- [x] Signal generation and filtering

### Phase 2: Trade Execution ✅
- [x] Signal → Trade execution pipeline
- [x] Risk management integration
- [x] IBKR order placement
- [x] Position tracking updates

### Phase 3: Exit Monitoring ✅
- [x] Position exit condition checks
- [x] Profit taking integration
- [x] Stop loss monitoring
- [x] Strategy exit logic

### Phase 4: Configuration & API ✅
- [x] Scheduler settings in config
- [x] API endpoints for control
- [x] Status reporting
- [x] Lifecycle management

### Phase 5: Error Handling & Resilience ✅
- [x] Graceful error handling
- [x] Retry logic for transient failures
- [x] Circuit breakers for repeated failures
- [x] Logging and metrics

### Phase 6: Testing & Validation 🔄
- [ ] Unit tests for scheduler logic
- [ ] Integration tests with mock IBKR
- [ ] End-to-end test with paper trading
- [ ] Performance testing

## Configuration

```python
class SchedulerSettings(BaseSettings):
    """Trading scheduler configuration"""
    enabled: bool = Field(default=False, description="Enable automatic trading scheduler")
    evaluation_interval: int = Field(default=60, description="Strategy evaluation interval (seconds)")
    exit_check_interval: int = Field(default=30, description="Exit condition check interval (seconds)")
    min_confidence: float = Field(default=0.5, description="Minimum confidence to execute trades")
    max_concurrent_trades: int = Field(default=5, description="Maximum concurrent trades")
    require_ibkr_connection: bool = Field(default=True, description="Require IBKR connection to run")
    market_hours_only: bool = Field(default=True, description="Only trade during market hours")
    
    class Config:
        env_prefix = "SCHEDULER_"
```

## API Endpoints

- `GET /api/scheduler/status` - Get scheduler status
- `POST /api/scheduler/start` - Start scheduler
- `POST /api/scheduler/stop` - Stop scheduler
- `POST /api/scheduler/pause` - Pause scheduler (maintains state)
- `POST /api/scheduler/resume` - Resume scheduler
- `GET /api/scheduler/stats` - Get scheduler statistics

## Dependencies

- StrategyEvaluator (existing)
- IBKRClient (existing)
- RiskManager (existing)
- DataProviderManager (existing)
- Metrics integration (existing)

## Testing Strategy

1. **Unit Tests**: Mock all external dependencies
2. **Integration Tests**: Use test IBKR connection
3. **Paper Trading**: Full end-to-end with paper account
4. **Metrics**: Verify all metrics are recorded correctly

## Future Enhancements

- Strategy-specific evaluation intervals
- Adaptive scheduling based on market volatility
- Parallel strategy evaluation
- Signal queuing and prioritization
- Backtest mode for scheduler

