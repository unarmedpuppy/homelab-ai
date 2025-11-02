#!/usr/bin/env python3
"""
Test Prometheus Metrics Endpoint
=================================

Test script to verify the /metrics endpoint returns valid Prometheus-formatted metrics.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import time
from typing import Dict, Any

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
METRICS_ENDPOINT = f"{BASE_URL}/api/monitoring/metrics"


def test_metrics_endpoint():
    """Test the metrics endpoint"""
    print("=" * 60)
    print("Testing Prometheus Metrics Endpoint")
    print("=" * 60)
    print(f"Endpoint: {METRICS_ENDPOINT}\n")
    
    try:
        # Make request
        response = requests.get(METRICS_ENDPOINT, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"Response Length: {len(response.content)} bytes\n")
        
        if response.status_code != 200:
            print(f"❌ Error: Got status code {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if 'text/plain' not in content_type:
            print(f"⚠️  Warning: Expected text/plain, got {content_type}")
        
        # Parse and validate Prometheus format
        metrics_text = response.text
        lines = metrics_text.strip().split('\n')
        
        print("=" * 60)
        print("Metrics Found:")
        print("=" * 60)
        
        metrics_found = {}
        current_metric = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                if line.startswith('# HELP'):
                    # Extract metric name from HELP line
                    parts = line.split()
                    if len(parts) >= 3:
                        metric_name = parts[2]
                        print(f"\n📊 {metric_name}")
                        metrics_found[metric_name] = {'help': ' '.join(parts[3:])}
                        current_metric = metric_name
                elif line.startswith('# TYPE'):
                    parts = line.split()
                    if len(parts) >= 3:
                        metric_name = parts[2]
                        metric_type = parts[3]
                        if metric_name in metrics_found:
                            metrics_found[metric_name]['type'] = metric_type
                            print(f"   Type: {metric_type}")
                continue
            
            # Metric data line
            if ' ' in line or '{' in line:
                # This is a metric with value
                if '{' in line:
                    # Has labels
                    metric_part, value = line.rsplit(' ', 1)
                    metric_name = metric_part.split('{')[0]
                    labels = metric_part.split('{')[1].rstrip('}')
                else:
                    # No labels
                    parts = line.split(' ', 1)
                    metric_name = parts[0]
                    value = parts[1] if len(parts) > 1 else '0'
                
                if metric_name not in metrics_found:
                    metrics_found[metric_name] = {}
                
                # Store sample value
                try:
                    value_float = float(value)
                    if 'samples' not in metrics_found[metric_name]:
                        metrics_found[metric_name]['samples'] = []
                    metrics_found[metric_name]['samples'].append(value_float)
                    
                    # Print sample (limit to first few)
                    if len(metrics_found[metric_name]['samples']) <= 3:
                        print(f"   Sample: {line[:80]}")
                except ValueError:
                    pass
        
        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        print(f"Total Metrics: {len(metrics_found)}")
        
        # Check for expected system metrics
        expected_metrics = [
            'system_uptime_seconds',
            'system_python_version_info',
            'system_application_info'
        ]
        
        print("\nExpected System Metrics:")
        all_found = True
        for metric in expected_metrics:
            if metric in metrics_found:
                print(f"  ✅ {metric}")
            else:
                print(f"  ❌ {metric} - NOT FOUND")
                all_found = False
        
        if all_found:
            print("\n✅ All expected system metrics found!")
        else:
            print("\n⚠️  Some expected metrics are missing")
        
        # Validate Prometheus format basics
        has_help = any('# HELP' in line for line in lines)
        has_type = any('# TYPE' in line for line in lines)
        has_data = any(line and not line.startswith('#') for line in lines)
        
        print("\nPrometheus Format Validation:")
        print(f"  Has HELP comments: {'✅' if has_help else '❌'}")
        print(f"  Has TYPE comments: {'✅' if has_type else '❌'}")
        print(f"  Has metric data: {'✅' if has_data else '❌'}")
        
        if has_help and has_type and has_data:
            print("\n✅ Prometheus format validation passed!")
            return True
        else:
            print("\n⚠️  Prometheus format validation issues detected")
            return False
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to {BASE_URL}")
        print("   Make sure the API server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_after_operations():
    """Test that metrics change after performing operations"""
    print("\n" + "=" * 60)
    print("Testing Metrics After Operations")
    print("=" * 60)
    
    try:
        # Get initial metrics
        initial_response = requests.get(METRICS_ENDPOINT, timeout=10)
        initial_text = initial_response.text
        
        # Make some API calls to generate metrics (if API request metrics are enabled)
        try:
            # Try to hit health endpoint
            requests.get(f"{BASE_URL}/api/monitoring/health", timeout=5)
            time.sleep(0.5)  # Brief delay
        except Exception:
            pass
        
        # Get metrics again
        final_response = requests.get(METRICS_ENDPOINT, timeout=10)
        final_text = final_response.text
        
        # Check if metrics changed (basic check)
        if initial_text != final_text:
            print("✅ Metrics changed after operations (expected)")
        else:
            print("ℹ️  Metrics unchanged (this is OK if API request metrics aren't enabled yet)")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Could not test metrics changes: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    success = test_metrics_endpoint()
    test_metrics_after_operations()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Metrics endpoint test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Metrics endpoint test had issues")
        sys.exit(1)

