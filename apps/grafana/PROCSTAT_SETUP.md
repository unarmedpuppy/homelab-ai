# Enabling Process Memory Tracking in Grafana

## Problem

Your Grafana dashboard shows aggregate RAM usage (86%), but you need to see which **non-Docker processes** are consuming memory.

## Solution: Enable procstat Plugin in Telegraf

The `procstat` plugin allows Telegraf to collect per-process memory and CPU metrics.

### Step 1: Edit Telegraf Configuration

```bash
# SSH into your server, then:
docker exec -it telegraf vi /etc/telegraf/telegraf.conf
```

### Step 2: Add procstat Input

Add this section after the `[[inputs.processes]]` section:

```toml
# Monitor all processes (may be resource-intensive)
[[inputs.procstat]]
  pattern = ".*"
  
# OR monitor specific high-memory processes:
[[inputs.procstat]]
  exe = [
    "/steamcmd/rust/RustDedicated",
    "/usr/bin/Xvfb",
    "influxd",
    "telegraf"
  ]
```

### Step 3: Restart Telegraf

```bash
docker restart telegraf
```

### Step 4: Verify Data Collection

Wait 1-2 minutes, then check if data is being collected:

```bash
docker exec influxdb influx -execute "SHOW MEASUREMENTS" -database telegraf | grep procstat
```

You should see `procstat` in the list.

## Alternative: Quick Manual Check

If you just need a quick check right now, run:

```bash
# On your server:
ps aux --sort=-%mem | head -20

# Or from your local machine:
bash scripts/connect-server.sh "ps aux --sort=-%mem | head -20"
```

This will show the top 20 processes by memory usage.

## Expected Results

Once procstat is enabled, the Grafana dashboard panel **"Top 30 System Processes by Memory (RSS)"** will show:

- Process Name
- Memory (RSS) - Resident Set Size (actual RAM used)
- Memory (VMS) - Virtual Memory Size
- CPU %

This will help you identify which non-Docker processes are consuming your 86% RAM.

## Performance Note

Monitoring all processes (`pattern = ".*"`) can be resource-intensive. Consider:

1. **Start with specific processes** (using `exe` parameter)
2. **Monitor only high-memory processes** you suspect
3. **Use pattern matching** to filter (e.g., `pattern = "rust|influx|telegraf"`)

