# Sync X/Twitter Bookmarks

**Job ID:** `6a6511cbbad9`

## Description

Fetches X/Twitter bookmarks twice daily and integrates new bookmarks into the shua-ledger knowledge base. Automatically categorizes bookmarks into AI/ML and Finance/Trading, adds them as individual markdown files, and syncs to Gitea.

## Schedule

Runs at **4am and 4pm CST** (10:00 and 22:00 UTC) every day.

## What It Does

1. Reads X/Twitter credentials from `~/.shua-ledger/.twitter-credentials`
2. Fetches all bookmarks using Bird CLI (`bird bookmarks --json --all`)
3. Compares against existing bookmarks in `data/x-bookmarks.json`
4. Categorizes new bookmarks:
   - **AI/ML**: Contains keywords like "ai", "llm", "claude", "codex", "agent", "machine learning", "neural", "gpt"
   - **Finance/Trading**: Contains keywords like "polymarket", "btc", "trading", "crypto", "stock", "market", "investment", "finance"
5. Creates individual markdown files for each new bookmark with:
   - Author username
   - Creation date
   - Tweet ID
   - Full tweet content
   - Attribution footer
6. Updates the summary file (`data/x-bookmarks/summary.md`) with current counts
7. Commits and pushes changes to Gitea repository

## Configuration

### Credentials File
```
~/.shua-ledger/.twitter-credentials
```

Format:
```
auth_token:<your-auth-token>
ct0:<your-ct0-token>
```

**Permissions:** 600 (owner read/write only)

### Script Location
```
/Users/aijenquist/.shua-ledger/bin/sync-bookmarks.sh
```

### Data Directory
```
~/.shua-ledger/data/
```

### Git Repository
```
ssh://gitea.server.unarmedpuppy.com:2223/homelab/shua-ledger.git
```

## Output Files

### Knowledge Base
- **AI/ML:** `~/.shua-ledger/data/knowledge/AI/ML/bookmark-<id>-<date>.md`
- **Finance/Trading:** `~/.shua-ledger/data/knowledge/Finance/Trading/bookmark-<id>-<date>.md`

### Data Files
- `data/x-bookmarks.json` - Complete bookmark collection
- `data/x-bookmarks/summary.md` - Summary with counts and metadata

## Monitoring

### Check Job Status
```bash
cronjob action='list'
```

### View Recent Runs
Check the dashboard at `/cron-jobs` for:
- Last run time
- Last status (success/failure)
- Next scheduled run
- Number of new bookmarks added

### Logs
Logs are delivered locally to the chat session. For persistent logs, the script can be modified to write to a file in `/tmp/` or a dedicated log directory.

## Related Documentation

- [shua-ledger README](../../shua-ledger/README.md)
- [Bird CLI Documentation](https://github.com/steipete/bird)
- [X/Twitter API](https://developer.twitter.com/en/docs)

## Troubleshooting

### "No new bookmarks found"
This is normal if no new bookmarks have been added since the last run. The script checks against existing bookmarks.

### "Authentication failed"
- Check that credentials in `~/.shua-ledger/.twitter-credentials` are still valid
- X/Twitter credentials expire periodically and may need refreshing
- See the Bird CLI documentation for authentication methods

### "Push failed"
- Check network connectivity to Gitea server
- Verify SSH key has proper permissions
- Check if the repository is accessible

## Future Enhancements

- Add support for additional categories (Productivity, Technical, etc.)
- Implement deduplication logic
- Add image/media attachment support
- Support for bookmark folders/collections
- Incremental updates instead of full fetch
- Add bookmark metadata (likes, retweets, replies)
