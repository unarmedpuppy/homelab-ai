# Cron Time Slot Validation System

## Overview

This document describes the time slot validation system for cron jobs in the homelab-ai infrastructure.

## Problem Statement

When creating cron jobs, users need to:
1. Avoid conflicts with existing jobs
2. Maintain minimum separation between jobs
3. Respect blackout windows (8pm-11pm CST)
4. Find available time slots quickly

## Solution

A Python-based analyzer tool that:
- Parses all existing cron jobs from `~/.hermes/cron/jobs.json`
- Calculates blocked times based on configurable rules
- Presents available time slots
- Suggests alternatives if requested time is blocked

## Components

### 1. Time Slot Validator Script

**Location**: `~/workspace/homelab-ai/scripts/analyze-cron-schedule.py`

**Features**:
- Parses cron schedules (supports standard format and special cases)
- Calculates 15-minute buffers around each job
- Blocks 8pm-11pm CST by default
- Shows available slots by hour
- Provides alternatives for blocked times

**Usage**:
```bash
# Full analysis
python3 ~/workspace/homelab-ai/scripts/analyze-cron-schedule.py

# Check specific time
python3 ~/workspace/homelab-ai/scripts/analyze-cron-schedule.py --time=17:00
```

### 2. Updated publish-cron-jobs Skill

**Location**: `~/.hermes/skills/cronjob/publish-cron-jobs/SKILL.md`

**Changes**:
- Added time slot validator section
- Integrated analyzer into workflow
- Provided examples and best practices

**Workflow**:
1. Run analyzer to see current schedule
2. Choose available time or get suggestions
3. Create cron job with validated time
4. Publish to dashboard

### 3. Documentation

**Location**: `~/workspace/homelab-ai/scripts/README-cron-analyzer.md`

Contains:
- Usage instructions
- Rules and configuration
- Integration guide
- Examples

## Rules

### Hard Rules (unless approved)
- **15-minute minimum separation** between any two jobs
- **No jobs between 8pm-11pm CST** (20:00-23:00)

### Recommended Practices
- **Business hours preference**: 6am-8pm CST
- **Spread jobs evenly** throughout the day
- **Avoid overlapping** buffers (jobs that run at same time)

## Implementation Details

### Algorithm

1. Load all enabled cron jobs from hermes storage
2. Parse cron schedules to extract execution times
3. Generate blocked times:
   - Each job time ± 15 minutes
   - All times in blackout window
4. Calculate available times
5. Present results grouped by hour
6. If requested time provided, check and suggest alternatives

### Cron Parsing

Supports:
- Standard format: `minute hour day month day_of_week`
- Special cases: `@daily`, `@weekly`, `@monthly`
- Lists: `0,30 9,17 * * *`
- Ranges: `0 9-17 * * *`
- Steps: `*/15 * * * *`
- Day of week conversion (cron 0=Sunday → our 0=Monday)

### Time Representation

- Internal: Tuple `(hour, minute)` where hour is 0-23
- Display: 12-hour format with AM/PM (e.g., "8:30am", "5:00pm")
- Blocked calculation: Convert to minutes from midnight for easy comparison

## Configuration

Customize rules by editing the script:

```python
# In analyze-cron-schedule.py

# Blackout window (hours in CST, 24-hour format)
BLACKOUT_START = 20  # 8pm
BLACKOUT_END = 23    # 11pm

# Minimum separation between jobs (minutes)
MIN_SEPARATION = 15
```

## Testing

The system has been tested with:
- Current cron jobs: morning_briefing (8:30am), sync-x-bookmarks (10:00am, 10:00pm)
- Various requested times including blocked and available slots
- Blackout window times
- Times close to existing jobs

## Future Enhancements

Potential improvements:
- Support for more complex cron expressions
- Weekend vs weekday separation rules
- Job duration consideration (long-running jobs need more buffer)
- Visual schedule calendar view
- Conflict detection when modifying existing jobs
- Integration with cronjob tool for automatic suggestions

## See Also

- [`publish-cron-jobs`](/skills/publish-cron-jobs) - Main skill documentation
- [`cronjob`](/skills/cronjob) - Hermes cron management
- `~/workspace/homelab-ai/scripts/README-cron-analyzer.md` - User guide
