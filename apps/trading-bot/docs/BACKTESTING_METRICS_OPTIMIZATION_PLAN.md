# Backtesting Engine Advanced Features - Implementation Plan

**Status**: 🔄 In Progress  
**Agent**: Auto  
**Started**: December 19, 2024  
**Estimated Time**: 30-40 hours

---

## Overview

Implement comprehensive performance metrics calculation and parameter optimization for the backtesting engine. This will enable:
- Detailed performance analysis (Sharpe ratio, drawdown, win rate, profit factor, etc.)
- Strategy parameter optimization via grid search
- Comparison of different parameter combinations
- Storage and retrieval of optimization results

**Current State**: 
- ✅ Database models exist (`Backtest`, `BacktestTrade`)
- ✅ Basic backtesting infrastructure exists
- ❌ Performance metrics calculation not implemented
- ❌ Parameter optimization not implemented
- ❌ Backtesting API route returns "not yet implemented"

**Goal**: Create comprehensive metrics calculator and parameter optimization engine that integrates with existing backtesting infrastructure.

---

## Architecture Overview

### Components

1. **Performance Metrics Calculator** (`src/core/backtesting/metrics.py`)
   - Calculate all performance metrics from backtest trades
   - Metrics: Sharpe ratio, max drawdown, win rate, profit factor, average win/loss, etc.
   - Support for equity curve analysis

2. **Parameter Optimization Engine** (`src/core/backtesting/optimizer.py`)
   - Grid search optimization
   - Parameter range definition
   - Optimization result storage and comparison
   - Support for multiple optimization objectives (Sharpe, return, win rate, etc.)

3. **Backtesting Service** (`src/core/backtesting/engine.py`)
   - Core backtesting logic (if not exists)
   - Integration with metrics calculator
   - Trade-by-trade simulation

4. **API Integration** (`src/api/routes/backtesting.py`)
   - Enhanced backtesting endpoints
   - Metrics endpoint
   - Optimization endpoint

---

## Implementation Tasks

### Phase 1: Performance Metrics Calculator (Week 1)

#### Task 1.1: Create Metrics Calculator Module
**File**: `src/core/backtesting/metrics.py`

**Components**:
- `BacktestMetrics` dataclass (result structure)
- `MetricsCalculator` class

**Key Methods**:
```python
class MetricsCalculator:
    def calculate(self, trades: List[BacktestTrade], initial_capital: float, 
                  start_date: datetime, end_date: datetime) -> BacktestMetrics
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Tuple[float, datetime, datetime]
    
    def calculate_win_rate(self, trades: List[BacktestTrade]) -> float
    
    def calculate_profit_factor(self, trades: List[BacktestTrade]) -> float
    
    def calculate_average_win_loss(self, trades: List[BacktestTrade]) -> Tuple[float, float]
    
    def build_equity_curve(self, trades: List[BacktestTrade], initial_capital: float) -> pd.Series
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float
    
    def calculate_calmar_ratio(self, total_return: float, max_drawdown: float) -> float
```

**Metrics to Calculate**:
1. **Sharpe Ratio**: Risk-adjusted returns (annualized)
2. **Maximum Drawdown**: Largest peak-to-trough decline (value, %, start date, end date)
3. **Win Rate**: Percentage of profitable trades
4. **Profit Factor**: Gross profit / gross loss
5. **Average Win/Loss**: Average profit per winning trade / average loss per losing trade
6. **Total Return**: Final capital / initial capital - 1 (absolute and %)
7. **Sortino Ratio**: Similar to Sharpe but only considers downside deviation
8. **Calmar Ratio**: Annual return / maximum drawdown
9. **Recovery Time**: Time to recover from maximum drawdown
10. **Equity Curve**: Portfolio value over time
11. **Trade Statistics**: Total trades, winning trades, losing trades
12. **Return Distribution**: Monthly/daily returns for analysis

**Patterns to Follow**:
- Use pandas/numpy for calculations
- Handle edge cases (no trades, all wins, all losses)
- Support risk-free rate configuration
- Return structured metrics object

#### Task 1.2: Integrate Metrics into Backtest Model
**File**: `src/data/database/models.py` (if needed)

**Changes**:
- Metrics already exist in Backtest model (max_drawdown, sharpe_ratio, win_rate, etc.)
- Ensure metrics are properly populated after backtest completion

**Integration Points**:
- After backtest completes, calculate metrics
- Store metrics in Backtest model
- Store detailed metrics in `results` JSON field

#### Task 1.3: Create Metrics Calculation Service
**File**: `src/core/backtesting/service.py` (optional, or add to existing backtesting module)

**Components**:
- Service class to orchestrate metrics calculation
- Integration with database models
- Cache calculations if needed

---

### Phase 2: Parameter Optimization Engine (Week 1-2)

#### Task 2.1: Create Parameter Space Definition
**File**: `src/core/backtesting/parameter_space.py`

**Components**:
- `ParameterRange` class (define parameter ranges)
- `ParameterSpace` class (collection of parameter ranges)
- Support for different range types: linear, log, categorical

**Key Methods**:
```python
class ParameterRange:
    def __init__(self, name: str, min_val: float, max_val: float, 
                 step: float = None, log_scale: bool = False)
    def generate_values(self) -> List[Any]

class ParameterSpace:
    def __init__(self, ranges: Dict[str, ParameterRange])
    def generate_combinations(self) -> List[Dict[str, Any]]
    def get_total_combinations(self) -> int
```

**Example**:
```python
# For SMA Strategy
space = ParameterSpace({
    'sma_short': ParameterRange(10, 50, step=5),
    'sma_long': ParameterRange(50, 200, step=10),
    'rsi_period': ParameterRange(10, 20, step=2),
    'entry_threshold': ParameterRange(0.001, 0.01, step=0.001)
})
```

#### Task 2.2: Create Optimization Engine
**File**: `src/core/backtesting/optimizer.py`

**Components**:
- `OptimizationEngine` class
- Grid search implementation
- Optimization result storage and comparison

**Key Methods**:
```python
class OptimizationEngine:
    def __init__(self, strategy_class: Type[BaseStrategy], 
                 data: pd.DataFrame, parameter_space: ParameterSpace,
                 initial_capital: float)
    
    async def optimize(self, objective: str = "sharpe_ratio",
                      max_workers: int = 4) -> OptimizationResult
    
    def _run_single_backtest(self, params: Dict[str, Any]) -> BacktestMetrics
    
    def _evaluate_objective(self, metrics: BacktestMetrics, objective: str) -> float

@dataclass
class OptimizationResult:
    best_params: Dict[str, Any]
    best_metrics: BacktestMetrics
    all_results: List[Tuple[Dict[str, Any], BacktestMetrics]]
    optimization_time: float
    total_combinations: int
```

**Optimization Objectives**:
- `sharpe_ratio`: Maximize Sharpe ratio
- `total_return`: Maximize total return
- `win_rate`: Maximize win rate
- `profit_factor`: Maximize profit factor
- `calmar_ratio`: Maximize Calmar ratio
- `custom`: User-defined objective function

**Patterns to Follow**:
- Use `concurrent.futures.ThreadPoolExecutor` or `ProcessPoolExecutor` for parallel execution
- Progress tracking (log every N combinations)
- Early stopping options (optional)
- Memory-efficient result storage

#### Task 2.3: Create Optimization Result Storage
**File**: `src/data/database/models.py` (if needed) or use existing Backtest model

**Approach**:
- Store optimization results as new Backtest records with special flag
- Or create `OptimizationRun` model to track optimization runs
- Store best parameters and all tested combinations

**Considerations**:
- Store parameter combinations and their metrics
- Support for comparing multiple optimization runs
- Storage efficiency (may have many combinations)

---

### Phase 3: Backtesting Engine Integration (Week 2)

#### Task 3.1: Review/Create Core Backtesting Engine
**File**: `src/core/backtesting/engine.py`

**Check**: If backtesting engine exists, integrate metrics. If not, create basic engine.

**Components** (if needed):
- `BacktestEngine` class
- Trade-by-trade simulation
- Position tracking
- Entry/exit logic

**Integration**:
- After each backtest, calculate metrics using `MetricsCalculator`
- Store metrics in Backtest model
- Return comprehensive results

#### Task 3.2: Integrate with Strategy System
**Files**: 
- `src/core/backtesting/engine.py`
- `src/core/strategy/registry.py`

**Integration**:
- Load strategy from registry
- Pass strategy configuration (including optimized parameters)
- Execute backtest using strategy
- Collect trades and calculate metrics

---

### Phase 4: API Integration (Week 2-3)

#### Task 4.1: Enhance Backtesting API Routes
**File**: `src/api/routes/backtesting.py`

**Endpoints to Create/Update**:

1. **POST `/api/backtesting/run`**
   - Run single backtest
   - Accept: strategy name, symbol, date range, parameters, initial capital
   - Return: Backtest results with full metrics

2. **POST `/api/backtesting/optimize`**
   - Run parameter optimization
   - Accept: strategy name, symbol, date range, parameter space, objective
   - Return: Optimization results (best params, metrics, all results)

3. **GET `/api/backtesting/{backtest_id}/metrics`**
   - Get detailed metrics for a completed backtest
   - Return: Full metrics breakdown

4. **GET `/api/backtesting/results/{backtest_id}`**
   - Get backtest results
   - Return: Trades, metrics, equity curve data

5. **GET `/api/backtesting/optimization/{optimization_id}`**
   - Get optimization results
   - Return: Best parameters, all tested combinations, comparison

**Request/Response Models**:
```python
class BacktestRequest(BaseModel):
    strategy: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    parameters: Dict[str, Any] = {}

class OptimizationRequest(BaseModel):
    strategy: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    parameter_space: Dict[str, Dict[str, Any]]  # Parameter ranges
    objective: str = "sharpe_ratio"
    max_workers: int = 4
```

**Patterns to Follow**:
- Use Pydantic models for request/response validation
- Async endpoints for long-running operations
- Background tasks for optimization (return job ID, poll for results)
- Proper error handling and validation

#### Task 4.2: Add Background Task Support (Optional)
**File**: `src/core/backtesting/tasks.py` (if using background tasks)

**Considerations**:
- For long optimizations, use background tasks
- Store job status in database
- Allow polling for results
- Support job cancellation

---

### Phase 5: Testing & Documentation (Week 3)

#### Task 5.1: Create Test Script
**File**: `scripts/test_backtesting_metrics.py`

**Tests**:
- Metrics calculation with sample trades
- Edge cases (no trades, all wins, all losses)
- Parameter optimization with simple strategy
- API endpoint testing
- Integration with database

#### Task 5.2: Documentation
**File**: `docs/BACKTESTING_METRICS_USAGE.md`

**Document**:
- Metrics explanation (what each metric means)
- How to run backtests with metrics
- How to run parameter optimization
- API usage examples
- Interpreting optimization results

---

## File Structure

```
src/core/backtesting/
├── __init__.py              # Exports
├── metrics.py               # MetricsCalculator, BacktestMetrics
├── optimizer.py             # OptimizationEngine, ParameterSpace
├── engine.py                # BacktestEngine (if needed)
├── service.py               # BacktestingService (optional)
└── parameter_space.py       # ParameterRange, ParameterSpace

src/api/routes/
└── backtesting.py           # Enhanced API endpoints

scripts/
└── test_backtesting_metrics.py  # Test script

docs/
└── BACKTESTING_METRICS_USAGE.md  # Documentation
```

---

## Dependencies

- `pandas`: Data manipulation and equity curve
- `numpy`: Numerical calculations (Sharpe ratio, etc.)
- `concurrent.futures`: Parallel optimization execution
- Existing: Database models, strategy system

---

## Success Criteria

✅ All performance metrics calculated correctly  
✅ Metrics stored in database after backtest  
✅ Parameter optimization runs successfully  
✅ Optimization results stored and retrievable  
✅ API endpoints return comprehensive metrics  
✅ Test script validates all functionality  
✅ Documentation complete and clear  

---

## Risk Mitigation

1. **Performance**: Optimization can be slow with many combinations
   - Use parallel execution
   - Support early stopping
   - Provide progress updates

2. **Memory**: Large optimization results
   - Store only top N results or summary statistics
   - Support pagination for results retrieval

3. **Edge Cases**: Handle scenarios with no trades, all losses, etc.
   - Validate inputs
   - Return meaningful defaults
   - Log warnings for unusual scenarios

---

## Next Steps

1. ✅ Create implementation plan (this document)
2. ✅ Create TODO tracking document
3. ⏳ Implement Phase 1: Performance Metrics Calculator
4. ⏳ Implement Phase 2: Parameter Optimization Engine
5. ⏳ Implement Phase 3: Backtesting Engine Integration
6. ⏳ Implement Phase 4: API Integration
7. ⏳ Implement Phase 5: Testing & Documentation
8. ⏳ Code review and testing
9. ⏳ Documentation cleanup

