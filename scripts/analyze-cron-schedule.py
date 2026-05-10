#!/usr/bin/env python3
"""
Cron Schedule Analyzer and Time Slot Validator

Analyzes existing cron jobs and finds available time slots for new jobs.
Implements:
- 15-minute minimum separation between jobs
- No jobs between 8pm-11pm CST (20:00-23:00)
- Presents available options to user
"""

import json
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass


@dataclass
class CronJob:
    name: str
    schedule: str
    days_of_week: Set[int]  # 0=Monday, 6=Sunday
    hour: int
    minute: int


def parse_cron_schedule(schedule: str) -> List[CronJob]:
    """Parse a cron schedule string and return list of CronJob objects."""
    # Handle special cases
    if schedule == "@daily":
        return [CronJob("daily", schedule, set(range(7)), 0, 0)]
    if schedule == "@weekly":
        return [CronJob("weekly", schedule, {0}, 0, 0)]
    if schedule == "@monthly":
        return [CronJob("monthly", schedule, set(range(7)), 0, 0)]
    
    # Parse standard cron format: minute hour day month day_of_week
    parts = schedule.split()
    if len(parts) != 5:
        return []
    
    minute_str, hour_str, day_str, month_str, dow_str = parts
    
    # Parse day of week (cron uses 0=Sunday, we'll convert to our format 0=Monday)
    def parse_dow(dow_str: str) -> Set[int]:
        days = set()
        for part in dow_str.split(','):
            if part == '*':
                days.update(range(7))
            elif '/' in part:
                base_range, step = part.split('/')
                start, end = map(int, base_range.split('-'))
                for i in range(start, end + 1, int(step)):
                    our_day = (i + 6) % 7
                    days.add(our_day)
            elif '-' in part:
                start, end = map(int, part.split('-'))
                for i in range(start, end + 1):
                    our_day = (i + 6) % 7
                    days.add(our_day)
            else:
                i = int(part)
                our_day = (i + 6) % 7
                days.add(our_day)
        return days
    
    # Parse hours (handle ranges and lists)
    hours = []
    for part in hour_str.split(','):
        if part == '*':
            hours = list(range(24))
            break
        elif '/' in part:
            base_range, step = part.split('/')
            start, end = map(int, base_range.split('-'))
            hours.extend(range(start, end + 1, int(step)))
        elif '-' in part:
            start, end = map(int, part.split('-'))
            hours.extend(range(start, end + 1))
        else:
            hours.append(int(part))
    
    # Parse minutes (handle ranges and lists)
    minutes = []
    for part in minute_str.split(','):
        if part == '*':
            minutes = list(range(60))
            break
        elif '/' in part:
            base_range, step = part.split('/')
            start, end = map(int, base_range.split('-'))
            minutes.extend(range(start, end + 1, int(step)))
        elif '-' in part:
            start, end = map(int, part.split('-'))
            minutes.extend(range(start, end + 1))
        else:
            minutes.append(int(part))
    
    # Create CronJob objects
    jobs = []
    days_of_week = parse_dow(dow_str)
    
    for hour in hours:
        for minute in minutes:
            jobs.append(CronJob(f"{schedule}_{hour}_{minute}", schedule, days_of_week, hour, minute))
    
    return jobs


def load_existing_cron_jobs() -> List[CronJob]:
    """Load existing cron jobs from hermes storage."""
    try:
        with open('/Users/aijenquist/.hermes/cron/jobs.json', 'r') as f:
            data = json.load(f)
        
        jobs = []
        for job in data.get('jobs', []):
            if not job.get('enabled', True):
                continue
            
            schedule = job.get('schedule', {}).get('expr', '')
            jobs.extend(parse_cron_schedule(schedule))
        
        return jobs
    except Exception as e:
        print(f"Error loading cron jobs: {e}")
        return []


def format_time(hour: int, minute: int) -> str:
    """Format time as 12-hour clock with AM/PM."""
    if hour == 0:
        return f"12:{minute:02d}am"
    elif hour < 12:
        return f"{hour}:{minute:02d}am"
    elif hour == 12:
        return f"12:{minute:02d}pm"
    else:
        return f"{hour-12}:{minute:02d}pm"


def time_diff_minutes(t1: Tuple[int, int], t2: Tuple[int, int]) -> int:
    """Calculate absolute difference in minutes between two times."""
    mins1 = t1[0] * 60 + t1[1]
    mins2 = t2[0] * 60 + t2[1]
    return abs(mins1 - mins2)


def analyze_schedule(requested_time: Tuple[int, int] = None):
    """Analyze current schedule and find available slots."""
    
    # Load existing jobs
    jobs = load_existing_cron_jobs()
    
    if not jobs:
        print("\nNo existing cron jobs found.")
        print("\n✅ You can schedule a job at any time (except 8pm-11pm CST).")
        return
    
    print("\n📊 Current Cron Jobs Schedule")
    print("═" * 60)
    
    # Group jobs by time
    time_groups: Dict[Tuple[int, int], List[CronJob]] = {}
    for job in jobs:
        key = (job.hour, job.minute)
        if key not in time_groups:
            time_groups[key] = []
        time_groups[key].append(job)
    
    # Print sorted by time
    for (hour, minute), job_list in sorted(time_groups.items()):
        time_str = format_time(hour, minute)
        # Show only the base name without the full cron expression
        base_names = sorted(set(j.name.split('_')[0] if '_' in j.name else j.name for j in job_list))
        print(f"  {time_str:8s} — {', '.join(base_names)}")
    
    print("\n🚫 Blackout Window (8pm-11pm CST)")
    print("─" * 60)
    print("  8:00pm - 11:00pm — Jobs not allowed (unless approved)")
    
    print("\n⏰ Blocked Times (15-min buffer around jobs)")
    print("─" * 60)
    
    # Print buffers - only show unique buffer ranges
    buffer_ranges: Dict[Tuple[int, int], List[str]] = {}  # (start_hour, start_min) -> list of reasons
    
    for job in jobs:
        base_mins = job.hour * 60 + job.minute
        
        # Find the range of blocked minutes
        start_mins = max(0, base_mins - 15)
        end_mins = min(24*60 - 1, base_mins + 15)
        
        start_hour, start_min = divmod(start_mins, 60)
        
        base_name = job.name.split('_')[0] if '_' in job.name else job.name
        
        if (start_hour, start_min) not in buffer_ranges:
            buffer_ranges[(start_hour, start_min)] = []
        buffer_ranges[(start_hour, start_min)].append(base_name)
    
    # Print unique buffer ranges
    for (start_hour, start_min), reasons in sorted(buffer_ranges.items()):
        if 20 <= start_hour < 23:
            continue  # Skip blackout window
        
        end_hour, end_min = start_hour, start_min + 30
        if end_min >= 60:
            end_hour += 1
            end_min -= 60
        
        if start_hour == end_hour:
            print(f"  {format_time(start_hour, start_min):8s} - {format_time(start_hour, end_min):8s} — buffer around {format_time(job.hour, job.minute)} ({', '.join(reasons)})")
        else:
            print(f"  {format_time(start_hour, start_min):8s} - {format_time(end_hour, end_min):8s} — buffer around {format_time(job.hour, job.minute)} ({', '.join(reasons)})")
    
    print("\n✅ Available Time Slots")
    print("═" * 60)
    
    # Generate blocked times set
    blocked = set()
    for job in jobs:
        base_mins = job.hour * 60 + job.minute
        for delta in range(-15, 16):
            new_mins = base_mins + delta
            if new_mins < 0:
                new_mins += 24 * 60
            elif new_mins >= 24 * 60:
                new_mins -= 24 * 60
            blocked.add((new_mins // 60, new_mins % 60))
    
    # Block blackout window
    for hour in range(20, 23):
        for minute in range(60):
            blocked.add((hour, minute))
    for minute in range(15):
        blocked.add((23, minute))
    
    # Find available times by hour
    available_by_hour: Dict[int, List[int]] = {}
    for hour in range(24):
        available_minutes = []
        for minute in range(60):
            if (hour, minute) not in blocked:
                available_minutes.append(minute)
        
        if available_minutes:
            available_by_hour[hour] = available_minutes
    
    # Print available slots by hour
    for hour in sorted(available_by_hour.keys()):
        minutes = available_by_hour[hour]
        if len(minutes) == 60:
            print(f"  {format_time(hour, 0):8s} — all minutes available")
        else:
            # Group consecutive minutes into ranges
            ranges = []
            if minutes:
                start = minutes[0]
                end = start
                for m in minutes[1:]:
                    if m == end + 1:
                        end = m
                    else:
                        if start == end:
                            ranges.append(f"{start:02d}")
                        else:
                            ranges.append(f"{start:02d}-{end:02d}")
                        start = end = m
                if start == end:
                    ranges.append(f"{start:02d}")
                else:
                    ranges.append(f"{start:02d}-{end:02d}")
            
            if not ranges:
                pass  # No available minutes
            elif len(ranges) <= 5:
                print(f"  {format_time(hour, 0):8s} — minutes: {', '.join(ranges)}")
            else:
                # Show first and last few ranges
                if len(ranges) > 10:
                    print(f"  {format_time(hour, 0):8s} — minutes: {', '.join(ranges[:5])} ... {', '.join(ranges[-3:])}")
                else:
                    print(f"  {format_time(hour, 0):8s} — minutes: {', '.join(ranges)}")
    
    # If requested time is provided, check it and suggest alternatives
    if requested_time:
        print("\n🔍 Requested Time Analysis")
        print("═" * 60)
        
        req_str = format_time(requested_time[0], requested_time[1])
        
        if requested_time in blocked:
            print(f"❌ Requested time {req_str} is blocked!")
            
            # Find closest available times
            all_times = [(h, m) for h in range(24) for m in range(60) if (h, m) not in blocked]
            available_sorted = sorted(all_times, key=lambda t: time_diff_minutes(t, requested_time))
            
            print(f"\n✅ Closest available alternatives:")
            for i, (hour, minute) in enumerate(available_sorted[:8]):
                diff = time_diff_minutes((hour, minute), requested_time)
                diff_str = f"{diff//60}h{diff%60}m" if diff >= 60 else f"{diff}m"
                print(f"  {i+1}. {format_time(hour, minute):8s} — {diff_str} away")
        else:
            print(f"✅ Requested time {req_str} is available!")
    
    print("\n" + "═" * 60)
    print("\n💡 Tip: Use the suggested time when creating your cron job:")
    print("   cronjob action='create' \\")
    print("     name='your-job' \\")
    print("     prompt='Your task...' \\")
    print("     schedule='0 <hour> * * *' \\")
    print("     deliver='local'")
    print()


def main():
    import sys
    
    # Parse command line arguments
    requested_time = None
    
    for arg in sys.argv[1:]:
        if arg.startswith('--time=') or arg.startswith('-t='):
            time_str = arg.split('=')[1]
        elif arg.startswith('--time ') or arg.startswith('-t '):
            time_str = sys.argv[sys.argv.index(arg) + 1]
        elif ':' in arg:
            time_str = arg
        else:
            continue
        
        # Parse time like "17:00" or "5pm"
        parts = time_str.lower().split(':')
        if len(parts) == 2:
            hour = int(parts[0])
            if 'pm' in parts[1]:
                hour += 12
                parts[1] = parts[1].replace('pm', '')
            elif 'am' in parts[1]:
                parts[1] = parts[1].replace('am', '')
            minute = int(parts[1])
            requested_time = (hour % 24, minute)
        elif len(parts) == 1:
            # Just hour
            hour = int(parts[0])
            if 'pm' in parts[0]:
                hour += 12
            requested_time = (hour % 24, 0)
    
    analyze_schedule(requested_time)


if __name__ == "__main__":
    main()
