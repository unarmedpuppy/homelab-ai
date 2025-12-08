# Task Registry

Persistent task list for tracking work across sessions.

## Status Legend
- `pending` - Not started, available to work on
- `in_progress` - Currently being worked on
- `blocked` - Waiting on something
- `completed` - Done

## Active Tasks

| ID | Task | Project | Status | Priority | Notes |
|----|------|---------|--------|----------|-------|
| T1 | Consolidate metrics system (8 files → 3) | trading-bot | pending | high | Biggest code quality win. See IMPLEMENTATION_ROADMAP.md |
| T2 | Remove backward compat duplication in strategy.py | trading-bot | pending | medium | Duplicate enums in src/core/strategy.py |
| T3 | Standardize import patterns | trading-bot | pending | low | Focus on sentiment providers |
| T4 | Add missing type hints | trading-bot | pending | low | range_bound.py, sentiment providers |
| T5 | Standardize error handling | trading-bot | pending | medium | Replace broad except Exception |
| T6 | WebSocket data producer integration | trading-bot | pending | high | Connect data to WS streams |
| T7 | UI WebSocket integration | trading-bot | pending | medium | Dashboard real-time updates |
| T8 | WebSocket testing | trading-bot | pending | medium | No WS tests currently |
| T9 | IBKR integration testing | trading-bot | pending | high | Paper trading validation |
| T10 | Strategy-to-execution pipeline | trading-bot | pending | high | Signal → order with safety checks |
| T11 | Sentiment provider base class | trading-bot | pending | medium | Reduce boilerplate in 13 providers |

## Completed Tasks

| ID | Task | Project | Completed | Notes |
|----|------|---------|-----------|-------|
| - | Agents system cleanup | agents | 2024-11-27 | Simplified from 600MB to 272KB |

---

## Priority Order

**Immediate (This Session):**
1. T1 - Metrics consolidation
2. T2 - Strategy.py cleanup

**Next Session:**
3. T6 - WebSocket producers
4. T9 - IBKR testing
5. T10 - Execution pipeline

**Later:**
- T3, T4, T5 - Style cleanup
- T7, T8 - UI and tests
- T11 - Provider refactor

---

*Last updated: 2024-11-27*
