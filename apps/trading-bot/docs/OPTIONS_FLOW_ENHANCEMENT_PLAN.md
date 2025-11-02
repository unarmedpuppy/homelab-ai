# Options Flow Analysis Enhancement - Implementation Plan

## Overview
Enhance the existing Unusual Whales integration with advanced options flow analysis, pattern recognition, and sentiment scoring capabilities.

## Current State Analysis

### Existing Functionality (unusual_whales.py)
✅ Basic UnusualWhalesClient
- Options flow fetching
- Market tide data
- Flow ratio calculation (simple bullish/bearish)
- Basic sentiment scoring
- Unusual activity detection

### What's Missing
❌ Pattern recognition (sweeps, blocks)
❌ Enhanced put/call ratio calculations (multiple timeframes)
❌ Options chain analysis
❌ Advanced sentiment scoring for aggregator integration
❌ Database persistence for enhanced data
❌ Comprehensive API endpoints
❌ Integration with sentiment aggregator

## Enhancement Plan

### Phase 1: Pattern Recognition & Detection
1. **Sweep Detection**
   - Identify options sweeps (multiple strikes executed simultaneously)
   - Detect coordinated large orders
   - Calculate sweep strength score

2. **Block Detection**
   - Identify large block trades (single large orders)
   - Filter by size thresholds
   - Classify as bullish/bearish blocks

3. **Pattern Recognition**
   - Call/Put spreads
   - Straddles/Strangles
   - Iron condors, butterflies
   - Unusual volume spikes

### Phase 2: Enhanced Metrics
1. **Put/Call Ratios**
   - Volume-based P/C ratio
   - Premium-based P/C ratio
   - Open interest P/C ratio
   - Multiple timeframes (1h, 4h, 24h, 7d)

2. **Options Chain Analysis**
   - Max pain calculation
   - Gamma exposure (GEX)
   - Delta-neutral positioning
   - Strike concentration analysis

### Phase 3: Sentiment Integration
1. **Enhanced Sentiment Scoring**
   - Weight by pattern strength
   - Time-decay weighting
   - Volume-weighted sentiment
   - Confidence scoring

2. **Aggregator Integration**
   - Create OptionsFlowSentimentProvider
   - Implement SymbolSentiment interface
   - Integrate with SentimentAggregator

### Phase 4: API & Database
1. **Database Enhancements**
   - Store sweep/block patterns
   - Historical P/C ratios
   - Options chain snapshots

2. **API Endpoints**
   - `/api/options-flow/{symbol}` - Comprehensive flow data
   - `/api/options-flow/{symbol}/sweeps` - Sweep detection
   - `/api/options-flow/{symbol}/blocks` - Block trades
   - `/api/options-flow/{symbol}/pc-ratio` - P/C ratios
   - `/api/options-flow/{symbol}/chain` - Chain analysis
   - `/api/options-flow/{symbol}/sentiment` - Options sentiment

## Implementation Steps

### Step 1: Enhance OptionsFlow Model
- Add fields: is_sweep, is_block, pattern_type, gex, max_pain
- Enhance OptionsFlow dataclass

### Step 2: Pattern Detection Module
- Create `pattern_detector.py`
- Implement sweep detection algorithm
- Implement block detection algorithm
- Pattern classification

### Step 3: Metrics Calculator
- Create `options_metrics.py`
- Put/Call ratio calculations
- Options chain analysis
- Max pain calculator
- GEX calculator

### Step 4: Enhanced Sentiment Provider
- Create `options_flow_sentiment.py`
- Implement sentiment provider interface
- Integration with aggregator

### Step 5: Database Models
- Enhance OptionsFlow table
- Add OptionsChainSnapshot table
- Add OptionsPatterns table

### Step 6: API Routes
- Create/update options flow routes
- Add new endpoints
- Response models

### Step 7: Testing
- Test pattern detection
- Test metrics calculations
- Test sentiment integration
- Integration tests

## Files to Create/Modify

### New Files
- `src/data/providers/options/pattern_detector.py`
- `src/data/providers/options/metrics_calculator.py`
- `src/data/providers/options/chain_analyzer.py`
- `src/data/providers/sentiment/options_flow_sentiment.py`
- `src/api/routes/options_flow.py`
- `scripts/test_options_flow_enhancement.py`

### Modified Files
- `src/data/providers/unusual_whales.py` (enhance)
- `src/data/database/models.py` (enhance OptionsFlow, add tables)
- `src/config/settings.py` (add options flow settings)
- `src/data/providers/sentiment/aggregator.py` (add options provider)

## Success Criteria
✅ Sweep and block detection working
✅ Enhanced P/C ratios for multiple timeframes
✅ Options chain analysis implemented
✅ Sentiment provider integrated with aggregator
✅ Comprehensive API endpoints available
✅ Database persistence working
✅ Test suite passing

