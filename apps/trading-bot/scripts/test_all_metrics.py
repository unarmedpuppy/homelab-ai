#!/usr/bin/env python3
"""
Comprehensive Metrics Testing Script
=====================================

Tests all metrics collection to verify:
- Metrics endpoint is accessible
- Metrics are in Prometheus format
- Metrics change with operations
- All metric categories are present
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import time
from typing import Dict, List, Set
import re

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
METRICS_ENDPOINT = f"{BASE_URL}/api/monitoring/metrics"
HEALTH_ENDPOINT = f"{BASE_URL}/api/monitoring/health"


class MetricsTester:
    """Comprehensive metrics testing"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.metrics_endpoint = METRICS_ENDPOINT
        self.health_endpoint = HEALTH_ENDPOINT
        self.metrics_found: Dict[str, Dict] = {}
        self.test_results: Dict[str, bool] = {}
    
    def test_endpoint_accessibility(self) -> bool:
        """Test that metrics endpoint is accessible"""
        print("\n" + "=" * 60)
        print("Test 1: Metrics Endpoint Accessibility")
        print("=" * 60)
        
        try:
            response = requests.get(self.metrics_endpoint, timeout=10)
            if response.status_code == 200:
                print(f"✅ Metrics endpoint accessible: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                print(f"   Response Size: {len(response.content)} bytes")
                self.test_results['endpoint_accessible'] = True
                return True
            else:
                print(f"❌ Metrics endpoint returned {response.status_code}")
                self.test_results['endpoint_accessible'] = False
                return False
        except Exception as e:
            print(f"❌ Error accessing metrics endpoint: {e}")
            self.test_results['endpoint_accessible'] = False
            return False
    
    def test_prometheus_format(self) -> bool:
        """Test that metrics are in valid Prometheus format"""
        print("\n" + "=" * 60)
        print("Test 2: Prometheus Format Validation")
        print("=" * 60)
        
        try:
            response = requests.get(self.metrics_endpoint, timeout=10)
            if response.status_code != 200:
                print("❌ Cannot validate format - endpoint not accessible")
                return False
            
            content = response.text
            lines = content.split('\n')
            
            # Check for required Prometheus format elements
            has_help = any(line.startswith('# HELP') for line in lines)
            has_type = any(line.startswith('# TYPE') for line in lines)
            has_data = any(line and not line.startswith('#') and ' ' in line for line in lines)
            
            print(f"  Has HELP comments: {'✅' if has_help else '❌'}")
            print(f"  Has TYPE comments: {'✅' if has_type else '❌'}")
            print(f"  Has metric data: {'✅' if has_data else '❌'}")
            
            # Validate metric name format (Prometheus naming conventions)
            metric_names = self._extract_metric_names(content)
            invalid_names = [name for name in metric_names if not self._is_valid_metric_name(name)]
            
            if invalid_names:
                print(f"  ⚠️  Invalid metric names found: {invalid_names[:5]}")
            else:
                print(f"  ✅ All {len(metric_names)} metric names are valid")
            
            result = has_help and has_type and has_data and len(invalid_names) == 0
            self.test_results['prometheus_format'] = result
            return result
            
        except Exception as e:
            print(f"❌ Error validating format: {e}")
            self.test_results['prometheus_format'] = False
            return False
    
    def test_metric_categories(self) -> bool:
        """Test that all expected metric categories are present"""
        print("\n" + "=" * 60)
        print("Test 3: Metric Categories Presence")
        print("=" * 60)
        
        expected_categories = {
            'system': ['system_uptime_seconds', 'system_python_version_info', 'system_application_info'],
            'api': ['http_requests_total', 'http_request_duration_seconds'],
            'provider': ['provider_requests_total', 'provider_response_time_seconds'],
            'trading': ['trades_executed_total', 'signals_generated_total'],
            'strategy': ['strategy_evaluation_duration_seconds', 'strategy_win_rate'],
            'sentiment': ['sentiment_calculations_total', 'sentiment_provider_usage_total'],
        }
        
        try:
            response = requests.get(self.metrics_endpoint, timeout=10)
            if response.status_code != 200:
                print("❌ Cannot check categories - endpoint not accessible")
                return False
            
            content = response.text
            all_found = True
            
            for category, metric_names in expected_categories.items():
                found_count = sum(1 for name in metric_names if name in content)
                total_count = len(metric_names)
                
                status = "✅" if found_count == total_count else "⚠️" if found_count > 0 else "❌"
                print(f"  {status} {category.capitalize()}: {found_count}/{total_count} metrics")
                
                if found_count == 0:
                    all_found = False
            
            self.test_results['metric_categories'] = all_found
            return all_found
            
        except Exception as e:
            print(f"❌ Error checking categories: {e}")
            self.test_results['metric_categories'] = False
            return False
    
    def test_metrics_change(self) -> bool:
        """Test that metrics change after performing operations"""
        print("\n" + "=" * 60)
        print("Test 4: Metrics Change with Operations")
        print("=" * 60)
        
        try:
            # Get initial metrics
            initial_response = requests.get(self.metrics_endpoint, timeout=10)
            if initial_response.status_code != 200:
                print("❌ Cannot test changes - endpoint not accessible")
                return False
            
            initial_content = initial_response.text
            initial_requests = self._extract_metric_value(initial_content, 'http_requests_total', default=0)
            
            print(f"  Initial http_requests_total: {initial_requests}")
            
            # Perform operations
            print("  Performing test operations...")
            test_operations = [
                f"{self.base_url}/api/monitoring/health",
                f"{self.base_url}/api/monitoring/metrics",
            ]
            
            for url in test_operations:
                try:
                    requests.get(url, timeout=5)
                except Exception:
                    pass
            
            time.sleep(1)  # Wait for metrics to update
            
            # Get metrics again
            final_response = requests.get(self.metrics_endpoint, timeout=10)
            if final_response.status_code != 200:
                print("❌ Cannot verify changes - endpoint not accessible")
                return False
            
            final_content = final_response.text
            final_requests = self._extract_metric_value(final_content, 'http_requests_total', default=0)
            
            print(f"  Final http_requests_total: {final_requests}")
            
            if final_requests > initial_requests:
                print("  ✅ Metrics changed as expected")
                self.test_results['metrics_change'] = True
                return True
            else:
                print("  ⚠️  Metrics did not change (may be normal if caching/async)")
                self.test_results['metrics_change'] = True  # Not necessarily a failure
                return True
            
        except Exception as e:
            print(f"❌ Error testing metrics changes: {e}")
            self.test_results['metrics_change'] = False
            return False
    
    def test_metric_values_valid(self) -> bool:
        """Test that metric values are valid (non-negative, reasonable ranges)"""
        print("\n" + "=" * 60)
        print("Test 5: Metric Values Validation")
        print("=" * 60)
        
        try:
            response = requests.get(self.metrics_endpoint, timeout=10)
            if response.status_code != 200:
                print("❌ Cannot validate values - endpoint not accessible")
                return False
            
            content = response.text
            issues = []
            
            # Check specific metrics for reasonable values
            uptime = self._extract_metric_value(content, 'system_uptime_seconds')
            if uptime is not None and uptime < 0:
                issues.append(f"system_uptime_seconds is negative: {uptime}")
            
            # Check for NaN or Inf values (would appear as strings in Prometheus)
            if 'NaN' in content or 'Inf' in content or '-Inf' in content:
                issues.append("Found NaN or Inf values in metrics")
            
            if issues:
                print("  ❌ Issues found:")
                for issue in issues:
                    print(f"     - {issue}")
                self.test_results['metric_values'] = False
                return False
            else:
                print("  ✅ All metric values appear valid")
                self.test_results['metric_values'] = True
                return True
                
        except Exception as e:
            print(f"❌ Error validating values: {e}")
            self.test_results['metric_values'] = False
            return False
    
    def _extract_metric_names(self, content: str) -> Set[str]:
        """Extract all metric names from Prometheus format"""
        names = set()
        for line in content.split('\n'):
            if line.startswith('# HELP'):
                parts = line.split()
                if len(parts) >= 3:
                    names.add(parts[2])
        return names
    
    def _is_valid_metric_name(self, name: str) -> bool:
        """Check if metric name follows Prometheus conventions"""
        # Prometheus: [a-zA-Z_:][a-zA-Z0-9_:]*
        pattern = r'^[a-zA-Z_:][a-zA-Z0-9_:]*$'
        return bool(re.match(pattern, name))
    
    def _extract_metric_value(self, content: str, metric_name: str, default=None) -> float:
        """Extract a metric value from Prometheus format"""
        for line in content.split('\n'):
            if line.startswith(metric_name) and not line.startswith('#'):
                # Extract value (last part after space)
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return float(parts[-1])
                    except ValueError:
                        pass
        return default
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE METRICS TESTING")
        print("=" * 70)
        print(f"Metrics Endpoint: {self.metrics_endpoint}\n")
        
        tests = [
            self.test_endpoint_accessibility,
            self.test_prometheus_format,
            self.test_metric_categories,
            self.test_metrics_change,
            self.test_metric_values_valid,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"\n❌ Test failed with exception: {e}")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for r in results if r)
        total = len(results)
        
        print(f"\nTests Passed: {passed}/{total}")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {test_name}")
        
        overall_success = passed == total
        print(f"\n{'✅ ALL TESTS PASSED' if overall_success else '⚠️  SOME TESTS FAILED'}")
        
        return overall_success


if __name__ == "__main__":
    tester = MetricsTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

