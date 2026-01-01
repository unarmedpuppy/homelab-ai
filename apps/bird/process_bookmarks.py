#!/usr/bin/env python3
"""
Bird Bookmark Processor

Fetches X/Twitter bookmarks using Bird CLI, categorizes them with AI,
and maintains a living document of technologies and learning resources.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from dateutil import parser as date_parser

# Configuration
DATA_DIR = Path("/app/data")
REPO_DIR = Path("/repo")  # Mounted git repo
LEARNING_DOC = REPO_DIR / "docs" / "learning-list.md"
PROCESSED_FILE = DATA_DIR / "processed.json"
BOOKMARKS_CACHE = DATA_DIR / "bookmarks.json"

AI_ROUTER_URL = os.getenv("AI_ROUTER_URL", "http://local-ai-router:8000")
AI_API_KEY = os.getenv("AI_API_KEY", "")  # Required for Local AI Router auth
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


def load_processed() -> set[str]:
    """Load set of already processed tweet IDs."""
    if PROCESSED_FILE.exists():
        try:
            data = json.loads(PROCESSED_FILE.read_text())
            return set(data.get("processed_ids", []))
        except Exception as e:
            log(f"Error loading processed file: {e}")
    return set()


def save_processed(processed_ids: set[str]):
    """Save set of processed tweet IDs."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "processed_ids": list(processed_ids),
        "last_updated": datetime.now().isoformat()
    }
    PROCESSED_FILE.write_text(json.dumps(data, indent=2))


def categorize_with_ai(tweets: list[dict]) -> dict:
    """
    Send tweets to AI for categorization and summarization.
    
    Returns structured data with categories:
    - technologies: Tools, frameworks, libraries to explore
    - concepts: Ideas, patterns, methodologies to learn
    - resources: Tutorials, articles, repos to read
    - projects: Project ideas or inspirations
    - other: Everything else
    """
    if not tweets:
        return {"technologies": [], "concepts": [], "resources": [], "projects": [], "other": []}
    
    # Build context from tweets
    tweet_summaries = []
    for t in tweets:
        author = t.get("author", {}).get("username", "unknown")
        text = t.get("text", "")[:500]  # Limit length
        tweet_id = t.get("id", "unknown")
        tweet_summaries.append(f"Tweet {tweet_id} by @{author}:\n{text}\n")
    
    tweets_context = "\n---\n".join(tweet_summaries)
    
    prompt = f"""You are a technical curator helping organize bookmarked tweets into a learning list.

Analyze these tweets and categorize each one. For each tweet, extract:
1. A brief summary (1 sentence)
2. The category: "technologies", "concepts", "resources", "projects", or "other"
3. Any specific technologies, tools, or topics mentioned
4. A priority score 1-5 (5 = must learn, 1 = nice to know)

Focus on:
- Programming languages, frameworks, libraries, tools
- AI/ML technologies and techniques
- Software architecture patterns
- Developer productivity tools
- Interesting projects or repos

TWEETS:
{tweets_context}

Respond with valid JSON in this exact format:
{{
  "items": [
    {{
      "tweet_id": "...",
      "summary": "...",
      "category": "technologies|concepts|resources|projects|other",
      "topics": ["topic1", "topic2"],
      "priority": 1-5,
      "url": "https://x.com/user/status/tweet_id"
    }}
  ]
}}"""

    try:
        response = requests.post(
            f"{AI_ROUTER_URL}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "X-Project": "bird-bookmark-processor",
                "X-User-ID": "bird-bot"
            },
            json={
                "model": "auto",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that categorizes technical content. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            },
            timeout=120
        )
        
        if response.status_code != 200:
            log(f"AI request failed: {response.status_code} - {response.text}")
            return {"technologies": [], "concepts": [], "resources": [], "projects": [], "other": []}
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse JSON from response (handle markdown code blocks)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        parsed = json.loads(content)
        items = parsed.get("items", [])
        
        # Group by category
        categorized = {"technologies": [], "concepts": [], "resources": [], "projects": [], "other": []}
        for item in items:
            cat = item.get("category", "other")
            if cat in categorized:
                categorized[cat].append(item)
            else:
                categorized["other"].append(item)
        
        log(f"Categorized {len(items)} items")
        return categorized
        
    except Exception as e:
        log(f"AI categorization error: {e}")
        return {"technologies": [], "concepts": [], "resources": [], "projects": [], "other": []}


def update_learning_document(categorized: dict, existing_content: str = "") -> str:
    """Generate updated learning document content."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Parse existing content to preserve manual additions
    # For now, we'll append new items
    
    sections = []
    sections.append(f"# Learning List\n\n_Auto-updated by Bird Bookmark Processor_\n_Last update: {now}_\n")
    
    # Technologies section
    if categorized.get("technologies"):
        sections.append("\n## Technologies to Explore\n")
        for item in sorted(categorized["technologies"], key=lambda x: x.get("priority", 0), reverse=True):
            priority = item.get("priority", 3)
            priority_emoji = ["", ".", "..", "...", "....", "....."][min(priority, 5)]
            topics = ", ".join(item.get("topics", []))
            url = item.get("url", "")
            sections.append(f"- [{priority_emoji}] **{topics}**: {item.get('summary', '')} [link]({url})")
    
    # Concepts section
    if categorized.get("concepts"):
        sections.append("\n## Concepts to Learn\n")
        for item in sorted(categorized["concepts"], key=lambda x: x.get("priority", 0), reverse=True):
            topics = ", ".join(item.get("topics", []))
            url = item.get("url", "")
            sections.append(f"- **{topics}**: {item.get('summary', '')} [link]({url})")
    
    # Resources section
    if categorized.get("resources"):
        sections.append("\n## Resources to Read\n")
        for item in categorized["resources"]:
            topics = ", ".join(item.get("topics", []))
            url = item.get("url", "")
            sections.append(f"- {item.get('summary', '')} ({topics}) [link]({url})")
    
    # Projects section
    if categorized.get("projects"):
        sections.append("\n## Project Ideas\n")
        for item in categorized["projects"]:
            url = item.get("url", "")
            sections.append(f"- {item.get('summary', '')} [link]({url})")
    
    # Other section
    if categorized.get("other"):
        sections.append("\n## Other Bookmarks\n")
        for item in categorized["other"]:
            url = item.get("url", "")
            sections.append(f"- {item.get('summary', '')} [link]({url})")
    
    return "\n".join(sections)


def git_commit_changes(message: str):
    """Commit changes to the mounted git repo."""
    git_name = os.getenv("GIT_USER_NAME", "Bird Bot")
    git_email = os.getenv("GIT_USER_EMAIL", "bird@server.unarmedpuppy.com")
    
    try:
        # Configure git
        subprocess.run(["git", "config", "user.name", git_name], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "config", "user.email", git_email], cwd=REPO_DIR, check=True)
        
        # Add and commit
        subprocess.run(["git", "add", str(LEARNING_DOC)], cwd=REPO_DIR, check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=REPO_DIR,
            capture_output=True
        )
        
        if result.returncode != 0:  # Changes exist
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=REPO_DIR,
                check=True
            )
            log(f"Committed: {message}")
            
            # Push if remote exists
            push_result = subprocess.run(
                ["git", "push"],
                cwd=REPO_DIR,
                capture_output=True,
                text=True
            )
            if push_result.returncode == 0:
                log("Pushed to remote")
            else:
                log(f"Push failed (may need manual push): {push_result.stderr}")
        else:
            log("No changes to commit")
            
    except subprocess.CalledProcessError as e:
        log(f"Git error: {e}")
    except Exception as e:
        log(f"Unexpected git error: {e}")


def process_once():
    """Run one processing cycle."""
    log("Starting bookmark processing...")
    
    # Load already processed IDs
    processed_ids = load_processed()
    log(f"Already processed: {len(processed_ids)} tweets")
    
    # Fetch bookmarks and likes
    bookmarks = fetch_bookmarks()
    likes = fetch_likes()
    
    # Combine and deduplicate
    all_tweets = {t.get("id"): t for t in bookmarks + likes}
    
    # Filter out already processed
    new_tweets = [t for tid, t in all_tweets.items() if tid not in processed_ids]
    log(f"New tweets to process: {len(new_tweets)}")
    
    if not new_tweets:
        log("No new tweets to process")
        return
    
    # Categorize with AI
    categorized = categorize_with_ai(new_tweets)
    
    # Count items
    total_items = sum(len(v) for v in categorized.values())
    if total_items == 0:
        log("AI returned no categorized items")
        return
    
    # Ensure docs directory exists
    LEARNING_DOC.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing content if any
    existing_content = ""
    if LEARNING_DOC.exists():
        existing_content = LEARNING_DOC.read_text()
    
    # Generate updated document
    new_content = update_learning_document(categorized, existing_content)
    
    # Write document
    LEARNING_DOC.write_text(new_content)
    log(f"Updated {LEARNING_DOC}")
    
    # Mark tweets as processed
    new_processed_ids = {t.get("id") for t in new_tweets if t.get("id")}
    processed_ids.update(new_processed_ids)
    save_processed(processed_ids)
    
    # Commit changes
    git_commit_changes(f"bird: Update learning list with {total_items} items")
    
    log("Processing complete!")


def main():
    """Main entry point."""
    log("Bird Bookmark Processor starting...")
    log(f"Mode: {RUN_MODE}")
    log(f"AI Router: {AI_ROUTER_URL}")
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
