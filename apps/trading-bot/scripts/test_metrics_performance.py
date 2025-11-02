#!/usr/bin/env python3
"""
Metrics Performance Testing Script
==================================

Tests the performance overhead of metrics collection.
Measures the impact of metrics on application performance.
"""

import sys
import os
import time
import statistics
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.metrics import (
    get_metrics_registry,
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    generate_metrics_output
)
from src.utils.metrics_trading import record_trade_executed
from src.utils.metrics_providers import record_provider_request
from src.config.settings import settings


def time_function(func, *args, **kwargs):
    """Time a function call"""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    duration = time.perf_counter() - start
    return result, duration


def benchmark_metric_creation(iterations: int = 1000) -> Dict:
    """Benchmark metric creation overhead"""
    print("=" * 60)
    print("Test 1: Metric Creation Overhead")
    print("=" * 60)
    
    durations = []
    
    for i in range(iterations):
        _, duration = time_function(
            get_or_create_counter,
            f'test_counter_{i % 10}',  # Reuse names to test caching
            'Test counter'
        )
        durations.append(duration * 1000)  # Convert to ms
    
    avg = statistics.mean(durations)
    median = statistics.median(durations)
    p95 = sorted(durations)[int(len(durations) * 0.95)]
    p99 = sorted(durations)[int(len(durations) * 0.99)]
    
    print(f"✅ Iterations: {iterations}")
    print(f"✅ Average: {avg:.4f} ms")
    print(f"✅ Median: {median:.4f} ms")
    print(f"✅ 95th percentile: {p95:.4f} ms")
    print(f"✅ 99th percentile: {p99:.4f} ms")
    
    return {
        'iterations': iterations,
        'avg_ms': avg,
        'median_ms': median,
        'p95_ms': p95,
        'p99_ms': p99
    }


def benchmark_metric_updates(iterations: int = 10000) -> Dict:
    """Benchmark metric update overhead"""
    print("\n" + "=" * 60)
    print("Test 2: Metric Update Overhead")
    print("=" * 60)
    
    # Create metrics once
    counter = get_or_create_counter('perf_counter', 'Performance counter')
    histogram = get_or_create_histogram('perf_histogram', 'Performance histogram')
    gauge = get_or_create_gauge('perf_gauge', 'Performance gauge')
    
    counter_durations = []
    histogram_durations = []
    gauge_durations = []
    
    for i in range(iterations):
        # Counter
        _, duration = time_function(counter.inc)
        counter_durations.append(duration * 1000)
        
        # Histogram
        _, duration = time_function(histogram.observe, 0.5)
        histogram_durations.append(duration * 1000)
        
        # Gauge
        _, duration = time_function(gauge.set, float(i))
        gauge_durations.append(duration * 1000)
    
    results = {}
    
    for name, durations in [
        ('counter', counter_durations),
        ('histogram', histogram_durations),
        ('gauge', gauge_durations)
    ]:
        avg = statistics.mean(durations)
        median = statistics.median(durations)
        p95 = sorted(durations)[int(len(durations) * 0.95)]
        
        print(f"\n{name.capitalize()}:")
        print(f"  Average: {avg:.4f} ms")
        print(f"  Median: {median:.4f} ms")
        print(f"  95th percentile: {p95:.4f} ms")
        
        results[name] = {
            'avg_ms': avg,
            'median_ms': median,
            'p95_ms': p95
        }
    
    return results


def benchmark_metrics_output(iterations: int = 100) -> Dict:
    """Benchmark metrics output generation"""
    print("\n" + "=" * 60)
    print("Test 3: Metrics Output Generation")
    print("=" * 60)
    
    # Create some metrics first
    for i in range(100):
        counter = get_or_create_counter(f'output_test_{i}', 'Output test')
        counter.inc(i)
    
    durations = []
    output_sizes = []
    
    for _ in range(iterations):
        output, duration = time_function(generate_metrics_output)
        durations.append(duration * 1000)
        output_sizes.append(len(output))
    
    avg_duration = statistics.mean(durations)
    avg_size = statistics.mean(output_sizes)
    p95_duration = sorted(durations)[int(len(durations) * 0.95)]
    
    print(f"✅ Iterations: {iterations}")
    print(f"✅ Average duration: {avg_duration:.4f} ms")
    print(f"✅ 95th percentile: {p95_duration:.4f} ms")
    print(f"✅ Average output size: {avg_size:.0f} bytes")
    print(f"✅ Throughput: {1000/avg_duration:.1f} outputs/sec")
    
    return {
        'avg_duration_ms': avg_duration,
        'p95_duration_ms': p95_duration,
        'avg_size_bytes': avg_size,
        'throughput_per_sec': 1000/avg_duration
    }


def benchmark_high_level_operations(iterations: int = 1000) -> Dict:
    """Benchmark high-level metric operations"""
    print("\n" + "=" * 60)
    print("Test 4: High-Level Operations")
    print("=" * 60)
    
    # Test trade execution recording
    trade_durations = []
    for i in range(iterations):
        _, duration = time_function(
            record_trade_executed,
            "test_strategy",
            "AAPL",
            "BUY"
        )
        trade_durations.append(duration * 1000)
    
    # Test provider request recording
    provider_durations = []
    for i in range(iterations):
        _, duration = time_function(
            record_provider_request,
            "twitter",
            success=True,
            cached=False
        )
        provider_durations.append(duration * 1000)
    
    results = {}
    
    for name, durations in [
        ('trade_execution', trade_durations),
        ('provider_request', provider_durations)
    ]:
        avg = statistics.mean(durations)
        median = statistics.median(durations)
        p95 = sorted(durations)[int(len(durations) * 0.95)]
        
        print(f"\n{name.replace('_', ' ').title()}:")
        print(f"  Average: {avg:.4f} ms")
        print(f"  Median: {median:.4f} ms")
        print(f"  95th percentile: {p95:.4f} ms")
        
        results[name] = {
            'avg_ms': avg,
            'median_ms': median,
            'p95_ms': p95
        }
    
    return results


def benchmark_concurrent_updates(iterations: int = 1000, threads: int = 10) -> Dict:
    """Benchmark concurrent metric updates"""
    print("\n" + "=" * 60)
    print(f"Test 5: Concurrent Updates ({threads} threads)")
    print("=" * 60)
    
    import threading
    
    counter = get_or_create_counter('concurrent_counter', 'Concurrent counter')
    histogram = get_or_create_histogram('concurrent_histogram', 'Concurrent histogram')
    
    def update_metrics():
        for _ in range(iterations // threads):
            counter.inc()
            histogram.observe(0.5)
    
    start = time.perf_counter()
    threads_list = []
    
    for _ in range(threads):
        t = threading.Thread(target=update_metrics)
        threads_list.append(t)
        t.start()
    
    for t in threads_list:
        t.join()
    
    duration = (time.perf_counter() - start) * 1000
    
    print(f"✅ Total duration: {duration:.2f} ms")
    print(f"✅ Operations: {iterations * 2}")  # counter + histogram
    print(f"✅ Throughput: {iterations * 2 / (duration / 1000):.0f} ops/sec")
    print(f"✅ Avg per operation: {duration / (iterations * 2):.4f} ms")
    
    return {
        'duration_ms': duration,
        'operations': iterations * 2,
        'throughput_per_sec': iterations * 2 / (duration / 1000),
        'avg_per_operation_ms': duration / (iterations * 2)
    }


def main():
    """Run all performance tests"""
    print("\n" + "=" * 60)
    print("METRICS PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"Metrics enabled: {settings.metrics.enabled}")
    print()
    
    if not settings.metrics.enabled:
        print("⚠️  Metrics are disabled. Enable with METRICS_ENABLED=true")
        print("   Some tests will still run but may not reflect real overhead.")
        print()
    
    results = {}
    
    try:
        results['creation'] = benchmark_metric_creation(1000)
        results['updates'] = benchmark_metric_updates(10000)
        results['output'] = benchmark_metrics_output(100)
        results['high_level'] = benchmark_high_level_operations(1000)
        results['concurrent'] = benchmark_concurrent_updates(1000, 10)
        
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print("\nKey Findings:")
        print(f"  • Metric creation: ~{results['creation']['avg_ms']:.4f} ms")
        print(f"  • Counter update: ~{results['updates']['counter']['avg_ms']:.4f} ms")
        print(f"  • Metrics output: ~{results['output']['avg_duration_ms']:.2f} ms")
        print(f"  • Concurrent ops: ~{results['concurrent']['throughput_per_sec']:.0f} ops/sec")
        
        print("\n✅ Performance tests completed")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

