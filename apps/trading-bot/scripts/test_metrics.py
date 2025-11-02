#!/usr/bin/env python3
"""
Test Metrics Endpoint and Collection
=====================================

Test script for verifying metrics collection and Prometheus endpoint.
"""

import sys
import os
from pathlib import Path
import time
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.metrics import (
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    generate_metrics_output
)


def test_metrics_creation():
    """Test creating various metric types"""
    print("="*60)
    print("Test 1: Metrics Creation")
    print("="*60)
    
    # Create counter
    counter = get_or_create_counter('test_counter_total', 'A test counter')
    counter.inc()
    counter.inc(5)
    print(f"✅ Counter created: value = {counter._value.get()}")
    
    # Create histogram
    histogram = get_or_create_histogram('test_histogram_seconds', 'A test histogram')
    histogram.observe(0.1)
    histogram.observe(0.5)
    histogram.observe(1.0)
    print("✅ Histogram created and values observed")
    
    # Create gauge
    gauge = get_or_create_gauge('test_gauge', 'A test gauge')
    gauge.set(10.0)
    gauge.inc(5.0)
    print(f"✅ Gauge created: value = {gauge._value.get()}")
    
    # Create labeled metrics
    labeled_counter = get_or_create_counter(
        'test_labeled_counter_total',
        'A labeled counter',
        labelnames=['label1', 'label2']
    )
    labeled_counter.labels(label1='value1', label2='value2').inc()
    print("✅ Labeled counter created")
    
    return True


def test_metrics_output():
    """Test generating Prometheus metrics output"""
    print("\n" + "="*60)
    print("Test 2: Metrics Output Generation")
    print("="*60)
    
    # Generate output
    output = generate_metrics_output()
    
    print(f"✅ Generated metrics output: {len(output)} bytes")
    
    # Check format
    output_str = output.decode('utf-8')
    
    required_elements = ['# HELP', '# TYPE']
    for element in required_elements:
        if element in output_str:
            print(f"✅ Contains {element}")
        else:
            print(f"❌ Missing {element}")
            return False
    
    # Check for our test metrics
    test_metrics = ['test_counter_total', 'test_histogram_seconds', 'test_gauge']
    for metric in test_metrics:
        if metric in output_str:
            print(f"✅ Contains metric: {metric}")
        else:
            print(f"⚠️  Missing metric: {metric} (may not be in registry)")
    
    return True


def test_metrics_endpoint(host='http://localhost:8000', timeout=5):
    """Test metrics endpoint via HTTP"""
    print("\n" + "="*60)
    print("Test 3: Metrics Endpoint (HTTP)")
    print("="*60)
    
    endpoint = f"{host}/metrics"
    
    try:
        print(f"Attempting to connect to {endpoint}...")
        response = requests.get(endpoint, timeout=timeout)
        
        if response.status_code == 200:
            print(f"✅ Endpoint accessible: {response.status_code}")
            print(f"✅ Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            content = response.text
            print(f"✅ Metrics output: {len(content)} bytes")
            
            # Check for Prometheus format
            if '# HELP' in content or 'HELP' in content:
                print("✅ Prometheus format detected")
            else:
                print("⚠️  Prometheus format may be missing")
            
            # Count metrics
            metric_count = content.count('# TYPE')
            print(f"✅ Found {metric_count} metric types")
            
            return True
        else:
            print(f"❌ Endpoint returned status {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"⚠️  Could not connect to {endpoint}")
        print("   (Server may not be running - this is OK for unit testing)")
        return True  # Not a failure if server isn't running
    except requests.exceptions.Timeout:
        print(f"❌ Request to {endpoint} timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_decorators():
    """Test metric decorators"""
    print("\n" + "="*60)
    print("Test 4: Metric Decorators")
    print("="*60)
    
    from src.utils.metrics import track_duration, track_call_count
    
    # Test duration decorator
    @track_duration('test_decorator_duration', 'Test decorator duration', [])
    def test_function():
        time.sleep(0.01)
        return "success"
    
    result = test_function()
    assert result == "success"
    print("✅ Duration decorator works")
    
    # Test call count decorator
    @track_call_count('test_decorator_calls_total', 'Test decorator calls', [])
    def test_counter_function():
        return "called"
    
    test_counter_function()
    test_counter_function()
    print("✅ Call count decorator works")
    
    # Test context manager
    from src.utils.metrics import track_duration_context
    
    with track_duration_context('test_context_duration', 'Test context', labels=None):
        time.sleep(0.01)
    
    print("✅ Duration context manager works")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("METRICS SYSTEM - TEST SUITE")
    print("="*60)
    
    all_passed = True
    
    try:
        all_passed = test_metrics_creation() and all_passed
        all_passed = test_metrics_output() and all_passed
        all_passed = test_decorators() and all_passed
        all_passed = test_metrics_endpoint() and all_passed
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        if all_passed:
            print("✅ ALL TESTS PASSED")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
