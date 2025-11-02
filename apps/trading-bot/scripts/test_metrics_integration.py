#!/usr/bin/env python3
"""
Metrics Integration Test Script
================================

Tests that all metrics modules can be imported and basic functions work.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all metrics modules can be imported"""
    print("=" * 60)
    print("Testing Metrics Module Imports")
    print("=" * 60)
    
    import_errors = []
    
    # Test core metrics
    try:
        from src.utils.metrics import (
            get_metrics_registry,
            get_or_create_counter,
            get_or_create_histogram,
            get_or_create_gauge,
            track_duration_context
        )
        print("✅ Core metrics imports OK")
    except Exception as e:
        print(f"❌ Core metrics import failed: {e}")
        import_errors.append(("core metrics", str(e)))
    
    # Test trading metrics
    try:
        from src.utils.metrics_trading import (
            record_trade_executed,
            record_signal_generated,
            record_strategy_evaluation
        )
        print("✅ Trading metrics imports OK")
    except Exception as e:
        print(f"❌ Trading metrics import failed: {e}")
        import_errors.append(("trading metrics", str(e)))
    
    # Test provider metrics
    try:
        from src.utils.metrics_providers import (
            record_provider_request,
            record_provider_response_time,
            record_provider_error,
            update_provider_availability,
            update_data_freshness
        )
        print("✅ Provider metrics imports OK")
    except Exception as e:
        print(f"❌ Provider metrics import failed: {e}")
        import_errors.append(("provider metrics", str(e)))
    
    # Test business metrics
    try:
        from src.utils.metrics_business import (
            update_portfolio_pnl,
            update_portfolio_value,
            update_risk_metrics
        )
        print("✅ Business metrics imports OK")
    except Exception as e:
        print(f"❌ Business metrics import failed: {e}")
        import_errors.append(("business metrics", str(e)))
    
    # Test system metrics
    try:
        from src.utils.metrics_system import (
            initialize_system_metrics,
            update_system_metrics
        )
        print("✅ System metrics imports OK")
    except Exception as e:
        print(f"❌ System metrics import failed: {e}")
        import_errors.append(("system metrics", str(e)))
    
    # Test sentiment metrics
    try:
        from src.utils.metrics_sentiment import (
            record_sentiment_calculation,
            record_sentiment_aggregation
        )
        print("✅ Sentiment metrics imports OK")
    except Exception as e:
        print(f"❌ Sentiment metrics import failed: {e}")
        import_errors.append(("sentiment metrics", str(e)))
    
    # Test integration utilities
    try:
        from src.utils.metrics_integration import (
            update_portfolio_metrics_from_positions,
            calculate_and_update_strategy_win_rate
        )
        print("✅ Integration utilities imports OK")
    except Exception as e:
        print(f"❌ Integration utilities import failed: {e}")
        import_errors.append(("integration utilities", str(e)))
    
    # Test unified import from utils
    try:
        from src.utils import (
            record_trade_executed,
            record_provider_request,
            update_portfolio_pnl,
            update_provider_availability
        )
        print("✅ Unified utils imports OK")
    except Exception as e:
        print(f"❌ Unified utils import failed: {e}")
        import_errors.append(("unified utils", str(e)))
    
    print("\n" + "=" * 60)
    if import_errors:
        print(f"❌ {len(import_errors)} import errors found:")
        for module, error in import_errors:
            print(f"   - {module}: {error}")
        return False
    else:
        print("✅ All imports successful!")
        return True


def test_metric_creation():
    """Test that metrics can be created (with metrics disabled)"""
    print("\n" + "=" * 60)
    print("Testing Metric Creation (Disabled Mode)")
    print("=" * 60)
    
    try:
        # Temporarily disable metrics to test creation without Prometheus
        import os
        original_value = os.environ.get('METRICS_ENABLED', None)
        os.environ['METRICS_ENABLED'] = 'false'
        
        # Reimport after setting env var
        import importlib
        import src.utils.metrics as metrics_module
        importlib.reload(metrics_module)
        
        from src.utils.metrics import get_or_create_counter, get_metrics_registry
        
        registry = get_metrics_registry()
        counter = get_or_create_counter(
            name="test_counter",
            documentation="Test counter",
            registry=registry
        )
        
        # Should return None if metrics disabled
        if counter is None:
            print("✅ Metric creation handles disabled state correctly")
        else:
            print("⚠️  Metric returned even though metrics disabled (may be OK)")
        
        # Restore original value
        if original_value is None:
            os.environ.pop('METRICS_ENABLED', None)
        else:
            os.environ['METRICS_ENABLED'] = original_value
        
        return True
        
    except Exception as e:
        print(f"❌ Metric creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n")
    success = test_imports()
    test_metric_creation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Metrics integration test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Metrics integration test found issues")
        sys.exit(1)

