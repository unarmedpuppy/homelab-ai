#!/usr/bin/env python3
"""
Bird Bookmark Processor

Fetches X/Twitter bookmarks and likes using Bird CLI and stores them
in a SQLite database for later viewing and querying by external agents.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from dateutil import parser as date_parser

from database import (
    DatabaseSession,
    Post,
    PostSource,
    Run,
    RunSource,
    RunStatus,
    complete_run,
    create_run,
    get_or_create_post,
    init_db,
)

# Configuration
DATA_DIR = Path("/app/data")
BOOKMARK_LIMIT = int(os.getenv("BOOKMARK_LIMIT", "50"))
RUN_MODE = os.getenv("RUN_MODE", "cron")
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "21600"))  # 6 hours


def log(message: str):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def run_bird_command(args: list[str]) -> tuple[bool, str]:
    """Run a Bird CLI command and return (success, output)."""
    cmd = ["bird"] + args
    log(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            log(f"Bird command failed: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    except subprocess.TimeoutExpired:
        log("Bird command timed out")
        return False, "Timeout"
    except Exception as e:
        log(f"Bird command error: {e}")
        return False, str(e)


def fetch_bookmarks() -> list[dict]:
    """Fetch bookmarks from X using Bird CLI."""
    success, output = run_bird_command([
        "bookmarks",
        "-n", str(BOOKMARK_LIMIT),
        "--json"
    ])
    
    if not success:
        log("Failed to fetch bookmarks")
        return []
    
    try:
        bookmarks = json.loads(output)
        log(f"Fetched {len(bookmarks)} bookmarks")
        return bookmarks
    except json.JSONDecodeError as e:
        log(f"Failed to parse bookmarks JSON: {e}")
        return []


def fetch_likes() -> list[dict]:
    """Fetch likes from X using Bird CLI."""
    success, output = run_bird_command([
        "likes",
        "-n", str(BOOKMARK_LIMIT),
        "--json"
    ])
    
    if not success:
        log("Failed to fetch likes")
        return []
    
    try:
        likes = json.loads(output)
        log(f"Fetched {len(likes)} likes")
        return likes
    except json.JSONDecodeError as e:
        log(f"Failed to parse likes JSON: {e}")
        return []


def parse_tweet_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse tweet date string to datetime."""
    if not date_str:
        return None
    try:
        return date_parser.parse(date_str)
    except Exception:
        return None


def extract_media_urls(tweet: dict) -> Optional[str]:
    """Extract media URLs from tweet and return as JSON string."""
    media = tweet.get("media", [])
    if not media:
        return None
    
    urls = []
    for item in media:
        if isinstance(item, dict):
            # Try various possible URL fields
            url = item.get("url") or item.get("media_url") or item.get("media_url_https")
            if url:
                urls.append(url)
        elif isinstance(item, str):
            urls.append(item)
    
    return json.dumps(urls) if urls else None


def store_tweet(db, tweet: dict, run_id: str, source: str) -> bool:
    """
    Store a single tweet in the database.
    Returns True if new tweet was stored, False if duplicate.
    """
    tweet_id = tweet.get("id")
    if not tweet_id:
        log(f"Tweet missing ID, skipping")
        return False
    
    # Extract author info
    author = tweet.get("author", {})
    author_username = author.get("username") or author.get("screen_name")
    author_display_name = author.get("name") or author.get("display_name")
    
    # Build tweet URL
    url = None
    if author_username and tweet_id:
        url = f"https://x.com/{author_username}/status/{tweet_id}"
    
    # Try to get or create post
    post, created = get_or_create_post(
        db,
        tweet_id=str(tweet_id),
        source=source,
        run_id=run_id,
        author_username=author_username,
        author_display_name=author_display_name,
        content=tweet.get("text"),
        url=url,
        media_urls=extract_media_urls(tweet),
        tweet_created_at=parse_tweet_date(tweet.get("created_at")),
    )
    
    if created:
        log(f"Stored new {source} {tweet_id} by @{author_username}")
    
    return created


def process_once():
    """Run one processing cycle."""
    log("Starting bookmark processing...")
    
    # Initialize database
    init_db()
    
    bookmarks = fetch_bookmarks()
    likes = fetch_likes()
    
    bookmark_ids = {t.get("id") for t in bookmarks if t.get("id")}
    like_ids = {t.get("id") for t in likes if t.get("id")}
    
    log(f"Fetched {len(bookmarks)} bookmarks, {len(likes)} likes")
    
    if not bookmarks and not likes:
        log("No tweets fetched")
        return
    
    if bookmarks and likes:
        run_source = RunSource.MIXED.value
    elif bookmarks:
        run_source = RunSource.BOOKMARKS.value
    else:
        run_source = RunSource.LIKES.value
    
    # Create a run and store tweets
    with DatabaseSession() as db:
        run = create_run(db, run_source)
        log(f"Created run {run.id}")
        
        new_count = 0
        error = None
        
        try:
            for tweet in bookmarks:
                if store_tweet(db, tweet, run.id, PostSource.BOOKMARK.value):
                    new_count += 1
            
            for tweet in likes:  # Upgrades to 'both' if already bookmarked
                if store_tweet(db, tweet, run.id, PostSource.LIKE.value):
                    new_count += 1
            
            db.commit()
            
            overlap = len(bookmark_ids & like_ids)
            log(f"Stored {new_count} new posts ({overlap} in both bookmarks and likes)")
            
        except Exception as e:
            error = str(e)
            log(f"Error storing tweets: {e}")
            db.rollback()
        
        # Complete the run
        complete_run(
            db,
            run,
            success=(error is None),
            error=error,
            post_count=new_count
        )
    
    log("Processing complete!")


def main():
    """Main entry point."""
    log("Bird Bookmark Processor starting...")
    log(f"Mode: {RUN_MODE}")
    log(f"Bookmark limit: {BOOKMARK_LIMIT}")
    
    # Verify Bird CLI is available
    success, output = run_bird_command(["--version"])
    if success:
        log(f"Bird version: {output.strip()}")
    else:
        log("WARNING: Bird CLI may not be properly configured")
    
    if RUN_MODE == "daemon":
        while True:
            try:
                process_once()
            except Exception as e:
                log(f"Processing error: {e}")
            
            log(f"Sleeping for {SLEEP_INTERVAL} seconds...")
            time.sleep(SLEEP_INTERVAL)
    else:
        # One-shot mode
        try:
            process_once()
        except Exception as e:
            log(f"Processing error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
