# Cron Schedule Analyzer

A Python script for analyzing existing cron jobs and finding available time slots for new jobs.

## Purpose

Before creating a new cron job, run this analyzer to:
- See all currently scheduled jobs
- Understand blocked times (15-min buffers around jobs + 8pm-11pm CST blackout)
- Find available time slots
- Get suggestions if your preferred time is blocked

## Usage

```bash
# Analyze current schedule
python3 ~/workspace/homelab-ai/scripts/analyze-cron-schedule.py

# Analyze with a requested time (checks if it's available)
python3 ~/workspace/homelab-ai/scripts/analyze-cron-schedule.py --time=17:00

# Alternative syntax
python3 ~/workspace/homelab-ai/scripts/analyze-cron-schedule.py -t 15:30
```

## Rules

The analyzer enforces these scheduling rules:

1. **15-minute minimum separation** between any two cron jobs
2. **No jobs between 8pm-11pm CST** (20:00-23:00) by default
3. **Weekday/weekend consideration** for recurring jobs

## Output

The script displays:
- Current cron jobs schedule with times
- Blackout windows
- Blocked times (buffers around existing jobs)
- Available time slots by hour
- If you specify a time: analysis and alternatives if blocked

## Configuration

To customize the rules, edit the constants in the script:

```python
BLACKOUT_START = 20  # 8pm CST
BLACKOUT_END = 23    # 11pm CST
MIN_SEPARATION = 15  # minutes
```

## Integration with publish-cron-jobs skill

When using the `publish-cron-jobs` skill, always run this analyzer first to find a valid time slot before creating the cron job.

## Example

```bash
$ python3 ~/workspace/homelab-ai/scripts/analyze-cron-schedule.py --time=20:30

📊 Current Cron Jobs Schedule
════════════════════════════════════════════════════════════
  8:30am   — morning_briefing
  10:00am  — sync-x-bookmarks
  10:00pm  — sync-x-bookmarks

🚫 Blackout Window (8pm-11pm CST)
────────────────────────────────────────────────────────────
  8:00pm - 11:00pm — Jobs not allowed (unless approved)

🔍 Requested Time Analysis
════════════════════════════════════════════════════════════
❌ Requested time 8:30pm is blocked!

✅ Closest available alternatives:
  1. 7:59pm   — 31m away
  2. 7:58pm   — 32m away
  3. 7:57pm   — 33m away
```

## See Also

- [`publish-cron-jobs`](/skills/publish-cron-jobs) - Skill for publishing cron jobs to dashboard
- [`cronjob`](/skills/cronjob) - Hermes cron job management tool
