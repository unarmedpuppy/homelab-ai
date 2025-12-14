# Phase 3: Automation (n8n Integration)

**Status**: Planned (after Phase 2)
**Goal**: Automate data collection and enable conversational interface via Telegram

---

## Overview

Phase 3 transforms Life OS from a manually-triggered system to an automated, always-on assistant. Jobin becomes accessible via Telegram and automatically aggregates data from various sources.

---

## n8n Workflows

### 1. Daily Data Aggregation

**Trigger**: Scheduled (e.g., 9 PM daily)

**Data Sources**:
| Source | Data | Method |
|--------|------|--------|
| Google Calendar | Day's events | Google Calendar API |
| Apple Screen Time | App usage | Shortcuts → webhook |
| GitHub | Commits pushed | GitHub API |
| Discord | Gaming activity | Discord API |
| Xbox | Games played | Xbox API |
| Fitbit/Apple Health | Steps, exercise | API |

**Output**: Aggregated JSON payload sent to processing workflow

**Workflow Steps**:
1. Trigger at 9 PM
2. Parallel fetch from all data sources
3. Merge results
4. Send to "Evening Processing" workflow

### 2. Evening Processing

**Trigger**: Webhook from Daily Aggregation

**Process**:
1. Receive aggregated data
2. Call Claude/Jobin with:
   - Aggregated data
   - Existing journal entry (if any)
   - Jobin persona instructions
3. Jobin generates:
   - Updated journal entry
   - Contact updates (if calendar had meetings)
   - Changelog
4. Commit to git
5. Send summary to Telegram

### 3. Morning Briefing

**Trigger**: Scheduled (e.g., 7 AM daily)

**Process**:
1. Pull today's calendar
2. Scan contacts for upcoming birthdays
3. Check open reminders
4. Review weekly goal progress
5. Generate briefing text
6. Send to Telegram

### 4. Telegram Interface

**Trigger**: Telegram webhook

**Capabilities**:
- "Hey Jobin, add note to John Smith: ..."
- "What's on my calendar today?"
- "Log that I finished reading [book]"
- "Remind me to call Mom next week"

**Implementation**:
1. Telegram Bot API receives message
2. Route to Claude with Jobin persona
3. Jobin processes command
4. Updates files in repo
5. Commits changes
6. Responds via Telegram

---

## Data Source Integration Details

### Google Calendar

```
Method: OAuth2 → Google Calendar API
Endpoint: /calendars/primary/events
Data needed: Today's events with attendees
```

**n8n Nodes**:
- Google Calendar node (native)
- Filter to today's events
- Extract: title, time, attendees, location

### Apple Screen Time

No direct API. Options:
1. **Shortcuts automation**: Create iOS Shortcut that runs daily, formats screen time, sends to n8n webhook
2. **Screenshots → OCR**: Less reliable

### GitHub Activity

```
Method: GitHub API
Endpoint: /users/{user}/events
Filter: PushEvent for today
```

**Data extracted**:
- Repos committed to
- Number of commits
- Commit messages summary

### Discord Presence

```
Method: Discord API (requires bot in servers)
Data: Game activity, voice channel time
```

Note: May need a small bot to track presence.

### Xbox Activity

```
Method: Xbox Live API
Endpoint: Activity history
Data: Games played, achievements
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                        n8n                            │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────┐ │
│  │ Data Sources │───▶│  Aggregator │───▶│  Claude  │ │
│  └─────────────┘    └─────────────┘    │  (Jobin) │ │
│        │                                └────┬─────┘ │
│        │                                     │       │
│  ┌─────▼─────┐                          ┌────▼────┐  │
│  │  Calendar │                          │   Git   │  │
│  │  Screen   │                          │ Commit  │  │
│  │  GitHub   │                          └────┬────┘  │
│  │  Discord  │                               │       │
│  │  Xbox     │                          ┌────▼────┐  │
│  └───────────┘                          │Telegram │  │
│                                         │   Bot   │  │
│                                         └─────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## Telegram Bot Design

### Commands

| Command | Description |
|---------|-------------|
| `/brief` | Get morning briefing |
| `/today` | Show today's journal |
| `/contact {name}` | Show contact info |
| `/note {name} {text}` | Add note to contact |
| `/log {text}` | Add to today's journal |
| `/remind {text}` | Create reminder |
| `/status` | System status |

### Natural Language

Jobin should understand:
- "Had coffee with John today" → Updates journal + contact
- "Remind me to call the dentist" → Creates reminder
- "What did I do yesterday?" → Summarizes yesterday's journal

---

## Security Considerations

1. **Git auth**: n8n needs write access to life-os repo
   - Option: Deploy key with write access
   - Option: GitHub App with limited scope

2. **API tokens**: Store securely in n8n credentials
   - Google OAuth tokens
   - GitHub PAT
   - Telegram bot token

3. **Telegram access**: Whitelist your user ID only

4. **Claude API**: Secure key storage in n8n

---

## Checklist

### Infrastructure
- [ ] n8n instance with required integrations
- [ ] Telegram bot created and configured
- [ ] Git write access from n8n
- [ ] Claude API access from n8n

### Workflows
- [ ] Daily aggregation workflow
- [ ] Evening processing workflow
- [ ] Morning briefing workflow
- [ ] Telegram command handler
- [ ] Error alerting workflow

### Integrations
- [ ] Google Calendar connected
- [ ] Screen Time shortcut created
- [ ] GitHub activity pulling
- [ ] Discord bot (optional)
- [ ] Xbox API (optional)

### Testing
- [ ] End-to-end daily cycle test
- [ ] Telegram commands all work
- [ ] Error handling verified
- [ ] Git commits are clean

---

## Success Criteria

Phase 3 complete when:
- [ ] Daily briefing arrives in Telegram at 7 AM
- [ ] Can interact with Jobin via Telegram naturally
- [ ] Data automatically aggregated from 2+ sources
- [ ] Evening summary generated without manual input
- [ ] All changes properly committed to git
