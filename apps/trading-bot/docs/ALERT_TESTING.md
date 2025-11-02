# Alert Testing Guide

**Status**: ✅ Complete  
**Last Updated**: December 19, 2024

---

## Overview

This guide covers various methods to test that alerts are configured correctly and will fire when expected conditions occur.

---

## Testing Methods

### 1. Prometheus UI Testing

**Access**: `http://localhost:9090/alerts`

#### View Alert Status

1. Navigate to Prometheus → Alerts
2. See all configured alerts and their current state:
   - **Inactive**: Condition not met
   - **Pending**: Condition met but `for` duration not reached
   - **Firing**: Alert is active

#### Force Alert Test

1. Go to Prometheus → Graph
2. Enter alert expression, e.g.:
   ```promql
   system_cpu_usage_percent > 90
   ```
3. Temporarily modify query to force true:
   ```promql
   100 > 90  # Always true
   ```
4. This will make alert fire (for testing UI only)

---

### 2. Modify Metric Values

#### Using Prometheus Recording Rules

Create temporary test rule in `prometheus/alerts.yml`:

```yaml
- record: test:system_cpu_usage_percent
  expr: 95  # Force CPU to 95%
```

Then test alert:
```yaml
- alert: TestHighCPU
  expr: test:system_cpu_usage_percent > 90
  for: 1m
```

**Clean Up**: Remove test rules after testing.

---

### 3. API-Based Testing

#### Send Test Alert to Alertmanager

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "critical",
      "component": "testing"
    },
    "annotations": {
      "summary": "This is a test alert",
      "description": "Testing alert routing and notifications"
    },
    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }]'
```

#### Verify Alert Received

```bash
# Check Alertmanager UI
curl http://localhost:9093/api/v1/alerts

# Should see test alert
```

---

### 4. Simulate Conditions

### Simulate High CPU

**Method 1: Stress Test (Linux/Mac)**
```bash
# Run CPU stress test
docker exec trading-bot-bot python -c "
import multiprocessing
def cpu_burn():
    while True:
        pass
for _ in range(multiprocessing.cpu_count()):
    multiprocessing.Process(target=cpu_burn).start()
"
# Wait for alert to fire
# Kill: docker exec trading-bot-bot pkill -f cpu_burn
```

**Method 2: Update Metric Directly** (requires code modification)
```python
from src.utils.system_metrics import get_system_metrics

cpu_gauge, _, _ = get_system_metrics()
cpu_gauge.set(95.0)  # Force to 95%
```

### Simulate High Memory

```bash
# Allocate memory
docker exec trading-bot-bot python -c "
data = []
for i in range(1000):
    data.append([0] * 1000000)  # Allocate ~1GB
import time
time.sleep(600)  # Hold for 10 minutes
"
```

### Simulate Errors

**Trigger API Errors**:
```bash
# Send invalid requests
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/invalid-endpoint
done
```

**Check Error Rate Alert**:
- Should fire if `rate(http_errors_total[5m]) > 0.1`

---

### 5. Load Testing

#### Generate API Load

```bash
# Install hey (HTTP load testing tool)
# brew install hey  # Mac
# apt-get install hey  # Linux

# Generate load
hey -n 1000 -c 10 http://localhost:8000/api/health

# Monitor metrics
curl http://localhost:8000/metrics | grep http_request_duration_seconds
```

#### Test Response Time Alert

If response time increases, `HighAPIResponseTime` should fire.

---

### 6. Trading-Specific Tests

### Simulate Broker Disconnection

**Method 1: Mock IBKR Client** (in test code)
```python
# Temporarily modify broker connection status
from src.utils.metrics_trading import update_broker_connection_status
update_broker_connection_status(False)  # Simulate disconnect
```

**Method 2: Stop IBKR Gateway**
```bash
# If using IBKR Gateway
docker stop ibkr-gateway
# Alert should fire after 2 minutes
```

### Simulate Trade Rejections

Create test endpoint that rejects trades:

```python
# In test code
from src.utils.metrics_trading import record_trade_rejected

# Simulate rejections
for _ in range(10):
    record_trade_rejected("insufficient_balance")
```

---

## Testing Checklist

### Pre-Production Testing

- [ ] All alerts configured in `alerts.yml`
- [ ] Alertmanager configured and connected
- [ ] Test each alert type:
  - [ ] System health (CPU, memory, disk)
  - [ ] API health (errors, response time)
  - [ ] Trading (rejections, broker, slippage)
  - [ ] Providers (errors, rate limits)
  - [ ] Strategy (evaluation time, win rate)
  - [ ] Risk (drawdown, limits)

### Notification Testing

- [ ] Email alerts received (check spam folder)
- [ ] Slack alerts received
- [ ] PagerDuty alerts received (if configured)
- [ ] Webhook endpoints called
- [ ] Alert resolved notifications sent

### Alert Behavior Testing

- [ ] Alerts fire when threshold exceeded
- [ ] Alerts resolve when condition clears
- [ ] `for` duration works correctly
- [ ] Alert grouping works (multiple instances)
- [ ] Repeat intervals respected
- [ ] Routing based on severity works

---

## Automated Testing Script

Create `scripts/test_alerts.py`:

```python
#!/usr/bin/env python3
"""Test alert configuration and firing"""

import requests
import time
import json

PROMETHEUS_URL = "http://localhost:9090"
ALERTMANAGER_URL = "http://localhost:9093"

def test_alert_exists(alertname):
    """Verify alert is configured"""
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/rules")
    rules = response.json()
    
    for group in rules.get("data", {}).get("groups", []):
        for rule in group.get("rules", []):
            if rule.get("name") == alertname:
                print(f"✅ Alert found: {alertname}")
                return True
    
    print(f"❌ Alert not found: {alertname}")
    return False

def send_test_alert():
    """Send test alert to Alertmanager"""
    alert = [{
        "labels": {
            "alertname": "TestAlert",
            "severity": "critical"
        },
        "annotations": {
            "summary": "Test alert",
            "description": "Testing alert system"
        }
    }]
    
    response = requests.post(
        f"{ALERTMANAGER_URL}/api/v1/alerts",
        json=alert
    )
    
    if response.status_code == 200:
        print("✅ Test alert sent")
        return True
    else:
        print(f"❌ Failed to send alert: {response.status_code}")
        return False

def main():
    """Run alert tests"""
    print("Testing Alert System\n")
    
    # Test alerts exist
    test_alerts = [
        "HighCPUUsage",
        "HighMemoryUsage",
        "BrokerDisconnected",
        "HighErrorRate"
    ]
    
    for alert in test_alerts:
        test_alert_exists(alert)
    
    # Test sending alert
    send_test_alert()

if __name__ == "__main__":
    main()
```

---

## Troubleshooting

### Alert Not Firing

1. **Check Alert Expression**:
   ```bash
   # Test in Prometheus Graph
   # http://localhost:9090/graph
   ```

2. **Check Alert Status**:
   ```bash
   curl http://localhost:9090/api/v1/alerts
   ```

3. **Check Prometheus Logs**:
   ```bash
   docker logs trading-bot-prometheus | grep -i alert
   ```

### Alert Firing Too Often

1. **Increase `for` Duration**: Alert must fire for longer before triggering
2. **Adjust Threshold**: Raise threshold slightly
3. **Add Grouping**: Use `group_by` in Alertmanager

### Notification Not Received

1. **Check Alertmanager Status**:
   ```bash
   curl http://localhost:9093/api/v1/alerts
   ```

2. **Check Alertmanager Logs**:
   ```bash
   docker logs trading-bot-alertmanager
   ```

3. **Verify Receiver Configuration**: Check `alertmanager.yml`

---

## Best Practices

1. **Test in Development First**: Always test alerts in dev environment
2. **Use Non-Critical Channels**: Test with email/Slack before PagerDuty
3. **Document Tests**: Keep record of what was tested and results
4. **Regular Reviews**: Test alerts monthly to ensure they still work
5. **Gradual Rollout**: Start with lenient thresholds, tighten over time

---

## Related Documentation

- **Alert Rules**: `prometheus/alerts.yml`
- **Alertmanager Setup**: `docs/ALERTMANAGER_SETUP.md`
- **Threshold Recommendations**: `docs/ALERT_THRESHOLDS.md`

---

**Last Updated**: December 19, 2024

