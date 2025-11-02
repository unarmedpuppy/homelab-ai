# Alertmanager Setup Guide

**Status**: ✅ Complete  
**Last Updated**: December 19, 2024

---

## Overview

This guide covers setting up Alertmanager for sending notifications when alerts fire. Alertmanager integrates with Prometheus to route alerts to various notification channels (email, Slack, PagerDuty, etc.).

---

## Quick Start

### 1. Add Alertmanager to docker-compose.yml

Add the Alertmanager service:

```yaml
alertmanager:
  image: prom/alertmanager:latest
  container_name: trading-bot-alertmanager
  command:
    - '--config.file=/etc/alertmanager/alertmanager.yml'
    - '--storage.path=/alertmanager'
    - '--web.external-url=http://localhost:9093'
  volumes:
    - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    - alertmanager-data:/alertmanager
  ports:
    - "9093:9093"
  restart: unless-stopped
  networks:
    - trading-bot-network
  depends_on:
    - prometheus

volumes:
  alertmanager-data:
```

### 2. Configure Prometheus to use Alertmanager

Update `prometheus/prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 3. Configure Notification Channels

Edit `alertmanager/alertmanager.yml` and uncomment/configure your desired receivers:

- **Email**: Uncomment `email_configs` and set SMTP settings
- **Slack**: Uncomment `slack_configs` and add your webhook URL
- **PagerDuty**: Uncomment `pagerduty_configs` and add your service key

### 4. Restart Services

```bash
docker-compose restart prometheus alertmanager
```

---

## Configuration Details

### Email Setup

1. **Gmail** (Recommended for testing):
   ```yaml
   smtp_smarthost: 'smtp.gmail.com:587'
   smtp_from: 'your-email@gmail.com'
   smtp_auth_username: 'your-email@gmail.com'
   smtp_auth_password: 'your-app-password'  # Use App Password, not regular password
   ```

2. **Custom SMTP**:
   ```yaml
   smtp_smarthost: 'smtp.example.com:587'
   smtp_from: 'alerts@example.com'
   smtp_auth_username: 'alerts@example.com'
   smtp_auth_password: 'password'
   ```

**Gmail App Password Setup**:
1. Go to Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate app password for "Mail"
4. Use this password in `smtp_auth_password`

### Slack Setup

1. **Create Slack Webhook**:
   - Go to https://api.slack.com/apps
   - Create new app → Incoming Webhooks
   - Enable Incoming Webhooks
   - Add webhook to workspace
   - Copy webhook URL

2. **Configure Alertmanager**:
   ```yaml
   slack_configs:
     - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
       channel: '#trading-bot-alerts'
       title: '🚨 Critical Alert'
       text: '{{ .GroupLabels.alertname }}\n{{ .CommonAnnotations.description }}'
       send_resolved: true
   ```

### PagerDuty Setup

1. **Create PagerDuty Service**:
   - Go to PagerDuty → Services → New Service
   - Choose "Prometheus" integration
   - Copy Integration Key

2. **Configure Alertmanager**:
   ```yaml
   pagerduty_configs:
     - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
       description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
   ```

### Webhook Setup (Custom Integration)

For custom integrations (Discord, Teams, etc.):

```yaml
webhook_configs:
  - url: 'https://your-webhook-endpoint.com/alerts'
    send_resolved: true
    http_config:
      basic_auth:
        username: 'user'
        password: 'pass'
```

---

## Alert Routing

Alerts are routed based on severity:

- **Critical**: Immediate notification, repeat every 1 hour
- **Warning**: Grouped, repeat every 6 hours
- **Info**: Grouped, repeat every 24 hours

### Custom Routing

Modify routing in `alertmanager.yml`:

```yaml
routes:
  # Route trading alerts to specific receiver
  - match:
      component: trading
    receiver: 'trading-team'
    continue: true
  
  # Route by alert name
  - match_re:
      alertname: '.*Provider.*'
    receiver: 'provider-alerts'
```

---

## Testing Alerts

### 1. Test Alert via Prometheus UI

1. Go to `http://localhost:9090/alerts`
2. Find an alert
3. Click "Add Labels" and add `severity: critical` to trigger
4. Wait for alert to fire
5. Check Alertmanager: `http://localhost:9093`

### 2. Test via API

```bash
# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "critical"
    },
    "annotations": {
      "summary": "Test alert",
      "description": "This is a test"
    }
  }]'
```

### 3. Test Notification Channels

**Email**: Send test alert and check inbox (and spam folder)

**Slack**: Send test alert and check Slack channel

**Webhook**: Monitor webhook endpoint logs

---

## Alertmanager UI

Access at: `http://localhost:9093`

Features:
- View active alerts
- Silence alerts
- View notification history
- Test notification routes

---

## Troubleshooting

### Alerts Not Sending

1. **Check Alertmanager Status**:
   ```bash
   docker logs trading-bot-alertmanager
   ```

2. **Verify Prometheus Configuration**:
   - Check `prometheus.yml` has `alerting.alertmanagers` configured
   - Restart Prometheus

3. **Check Alert Status**:
   - Prometheus: `http://localhost:9090/alerts`
   - Alertmanager: `http://localhost:9093`

### Email Not Working

1. **Verify SMTP Settings**:
   - Test with `telnet smtp.gmail.com 587`
   - Use App Password for Gmail (not regular password)

2. **Check Logs**:
   ```bash
   docker logs trading-bot-alertmanager | grep -i email
   ```

### Slack Not Working

1. **Verify Webhook URL**:
   ```bash
   curl -X POST YOUR_WEBHOOK_URL -d '{"text":"test"}'
   ```

2. **Check Slack App Permissions**:
   - Incoming Webhooks must be enabled

---

## Security Considerations

1. **Credentials**: Use environment variables or secrets management for passwords
2. **TLS**: Use HTTPS for webhook URLs in production
3. **Access Control**: Consider authentication for Alertmanager UI in production

### Using Environment Variables

Update `docker-compose.yml`:

```yaml
alertmanager:
  environment:
    - SMTP_AUTH_USERNAME=${SMTP_USERNAME}
    - SMTP_AUTH_PASSWORD=${SMTP_PASSWORD}
```

Update `alertmanager.yml`:

```yaml
smtp_auth_username: '${SMTP_AUTH_USERNAME}'
smtp_auth_password: '${SMTP_AUTH_PASSWORD}'
```

---

## Best Practices

1. **Group Related Alerts**: Use `group_by` to prevent alert storms
2. **Set Reasonable Intervals**: Balance between immediate alerts and notification fatigue
3. **Use Severity Levels**: Route critical alerts differently from warnings
4. **Test Regularly**: Periodically test alert routing and notifications
5. **Document**: Keep track of which alerts go to which teams/channels

---

## Reference

- **Alertmanager Docs**: https://prometheus.io/docs/alerting/latest/alertmanager/
- **Configuration**: `alertmanager/alertmanager.yml`
- **Prometheus Alerts**: `prometheus/alerts.yml`

---

**Last Updated**: December 19, 2024

