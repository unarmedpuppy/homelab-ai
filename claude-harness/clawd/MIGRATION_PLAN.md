# Avery Agent Migration Plan

> Migrating from clawdbot to a standalone, dockerized agent system with n8n orchestration.

## Overview

This document provides everything needed to build a standalone "Avery" agent that replicates clawdbot's functionality:

1. **iMessage integration** via `imsg` CLI
2. **Google integration** (Calendar, Gmail) via `gog` CLI
3. **Twilio voice** via custom webhook server
4. **Personality injection** via markdown files
5. **Memory persistence** via filesystem
6. **Scheduling** via n8n (replaces clawdbot heartbeats/cron)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mac Mini Host                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   n8n (docker)  │    │ twilio-webhook  │                    │
│  │                 │    │    (docker)     │                    │
│  │  - Schedules    │    │                 │                    │
│  │  - Webhooks     │    │  - Voice calls  │                    │
│  │  - Workflows    │    │  - TwiML        │                    │
│  └────────┬────────┘    └─────────────────┘                    │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────┐                   │
│  │         avery-agent (docker)            │                   │
│  │                                         │                   │
│  │  - Polls imsg for messages              │                   │
│  │  - Loads personality (SOUL, IDENTITY)   │                   │
│  │  - Calls Claude API                     │                   │
│  │  - Executes tool calls (gog, imsg)      │                   │
│  │  - Writes to memory files               │                   │
│  └─────────────────────────────────────────┘                   │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────┐                   │
│  │              Shared Volumes             │                   │
│  │                                         │                   │
│  │  /data/personality/  (SOUL.md, etc.)    │                   │
│  │  /data/memory/       (daily logs)       │                   │
│  │  /data/config/       (credentials)      │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: iMessage Integration

### Overview

The `imsg` CLI reads from and writes to macOS Messages. It requires **Full Disk Access** to read `~/Library/Messages/chat.db`.

### Installation

```bash
# Install via Homebrew (if available) or download binary
brew install imsg  # or download from releases
```

### Key Commands

#### List Chats
```bash
imsg chats
# Returns list of chat IDs, participants, last message
```

#### Watch for Incoming Messages (Streaming)
```bash
imsg watch --json
# Streams new messages as JSON to stdout

# Filter to specific chat:
imsg watch --chat-id 4 --json

# With attachments:
imsg watch --chat-id 4 --attachments --json
```

**Output format:**
```json
{
  "rowid": 12345,
  "chat_id": 4,
  "sender": "+16512367878",
  "text": "Hey, what's for dinner?",
  "date": "2026-01-26T18:30:00Z",
  "is_from_me": false
}
```

#### Get Chat History
```bash
imsg history --chat-id 4 --limit 10 --json

# With date range:
imsg history --chat-id 4 --start 2026-01-26T00:00:00Z --json
```

#### Send Message
```bash
# To phone number:
imsg send --to "+16512367878" --text "Hello!"

# To chat ID (for group chats):
imsg send --chat-id 4 --text "Hello everyone!"

# With attachment:
imsg send --to "+16512367878" --text "Check this out" --file ~/photo.jpg
```

### Important Notes

- **Group chats**: Always use `--chat-id` not `--to` for group messages
- **Chat ID vs Phone**: Same person may appear in multiple chats (direct + group)
- **Full Disk Access**: Required for the process running imsg
- **Service**: Use `--service imessage` or `--service sms` to force protocol

### Polling Script Pattern

```python
#!/usr/bin/env python3
"""
imsg_poller.py - Poll iMessage for new messages and route to agent
"""

import subprocess
import json
import time
from datetime import datetime

class IMsgPoller:
    def __init__(self, agent_callback):
        self.agent_callback = agent_callback
        self.last_rowid = self._get_latest_rowid()

    def _get_latest_rowid(self):
        """Get the most recent message rowid to start from"""
        result = subprocess.run(
            ['imsg', 'history', '--chat-id', '4', '--limit', '1', '--json'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            messages = json.loads(result.stdout)
            if messages:
                return messages[0].get('rowid', 0)
        return 0

    def poll(self):
        """Check for new messages since last poll"""
        result = subprocess.run(
            ['imsg', 'history', '--chat-id', '4', '--limit', '20', '--json'],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            return []

        messages = json.loads(result.stdout)
        new_messages = [
            m for m in messages
            if m.get('rowid', 0) > self.last_rowid
            and not m.get('is_from_me', False)
        ]

        if new_messages:
            self.last_rowid = max(m.get('rowid', 0) for m in new_messages)

        return new_messages

    def send(self, chat_id: int, text: str):
        """Send a message to a chat"""
        subprocess.run([
            'imsg', 'send',
            '--chat-id', str(chat_id),
            '--text', text
        ])

    def run(self, poll_interval: float = 2.0):
        """Main polling loop"""
        print(f"Starting iMessage poller (interval: {poll_interval}s)")
        while True:
            try:
                new_messages = self.poll()
                for msg in new_messages:
                    print(f"New message from {msg.get('sender')}: {msg.get('text')}")
                    response = self.agent_callback(msg)
                    if response:
                        self.send(msg.get('chat_id'), response)
            except Exception as e:
                print(f"Poll error: {e}")

            time.sleep(poll_interval)
```

### Alternative: Watch Mode (Streaming)

```python
#!/usr/bin/env python3
"""
imsg_watcher.py - Stream iMessage using watch mode
"""

import subprocess
import json

def watch_messages(agent_callback):
    """Stream messages using imsg watch"""
    process = subprocess.Popen(
        ['imsg', 'watch', '--json'],
        stdout=subprocess.PIPE,
        text=True
    )

    for line in process.stdout:
        try:
            msg = json.loads(line.strip())
            if not msg.get('is_from_me', False):
                response = agent_callback(msg)
                if response:
                    send_message(msg.get('chat_id'), response)
        except json.JSONDecodeError:
            continue

def send_message(chat_id: int, text: str):
    subprocess.run([
        'imsg', 'send',
        '--chat-id', str(chat_id),
        '--text', text
    ])
```

---

## Part 2: Google Integration (gog CLI)

### Overview

The `gog` CLI provides access to Google Workspace APIs. It uses OAuth2 and stores tokens locally.

### Installation & Auth

```bash
# Install
brew install gog  # or download binary

# Authenticate (opens browser)
gog auth login --account aijenquist@gmail.com

# Verify
gog auth status
```

### Calendar Commands

#### List Calendars
```bash
gog calendar calendars --account aijenquist@gmail.com --json
```

#### List Events
```bash
# Next 7 days from specific calendar
gog calendar events "CALENDAR_ID" \
  --account aijenquist@gmail.com \
  --from "2026-01-26" \
  --to "2026-02-02" \
  --json

# Today only
gog calendar events "CALENDAR_ID" \
  --account aijenquist@gmail.com \
  --today \
  --json

# Next N days
gog calendar events "CALENDAR_ID" \
  --account aijenquist@gmail.com \
  --days 7 \
  --json
```

#### Create Event
```bash
gog calendar create "CALENDAR_ID" \
  --account aijenquist@gmail.com \
  --summary "Team Meeting" \
  --from "2026-01-27T10:00:00" \
  --to "2026-01-27T11:00:00" \
  --json
```

#### Update Event
```bash
gog calendar update "CALENDAR_ID" "EVENT_ID" \
  --account aijenquist@gmail.com \
  --summary "Updated Title" \
  --json
```

#### Delete Event
```bash
gog calendar delete "CALENDAR_ID" "EVENT_ID" \
  --account aijenquist@gmail.com \
  --force
```

### Gmail Commands

#### Search Emails
```bash
# Unread emails from last day
gog gmail search "is:unread newer_than:1d" \
  --account aijenquist@gmail.com \
  --max 10 \
  --json

# From specific sender
gog gmail search "from:someone@example.com" \
  --account aijenquist@gmail.com \
  --json

# With label
gog gmail search "label:important is:unread" \
  --account aijenquist@gmail.com \
  --json
```

#### Get Message Details
```bash
gog gmail get "MESSAGE_ID" \
  --account aijenquist@gmail.com \
  --json
```

#### Send Email
```bash
gog gmail send \
  --account aijenquist@gmail.com \
  --to "recipient@example.com" \
  --subject "Hello" \
  --body "Message body here"
```

### Config Location

```
# macOS
~/Library/Application Support/gogcli/config.json

# Tokens stored in system keyring
```

### Tool Definition for Agent

```json
{
  "name": "google_calendar",
  "description": "Manage Google Calendar events",
  "parameters": {
    "action": {
      "type": "string",
      "enum": ["list", "create", "update", "delete"]
    },
    "calendar_id": {
      "type": "string",
      "description": "Calendar ID (use configured family calendar by default)"
    },
    "from_date": { "type": "string" },
    "to_date": { "type": "string" },
    "summary": { "type": "string" },
    "event_id": { "type": "string" }
  }
}
```

---

## Part 3: Twilio Voice Integration

### Overview

Twilio voice calls require a webhook server that returns TwiML (Twilio Markup Language). The server handles:

1. Incoming call → greeting
2. Speech input → process → response
3. Hangup

### Current Implementation

**File:** `twilio-webhook/server.js`

```javascript
const http = require('http');
const { URL, URLSearchParams } = require('url');

const PORT = 8080;
const BASE_URL = 'https://your-domain.ts.net'; // Tailscale funnel or ngrok

function escapeXml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function parseBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => resolve(new URLSearchParams(body)));
  });
}

function twiml(content) {
  return `<?xml version="1.0" encoding="UTF-8"?><Response>${content}</Response>`;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const params = await parseBody(req);

  res.setHeader('Content-Type', 'text/xml');

  // Initial call - greeting
  if (url.pathname === '/voice' || url.pathname === '/voice/') {
    res.end(twiml(`
      <Say voice="Polly.Joanna">Hello, this is Avery. How can I help?</Say>
      <Gather input="speech" action="${BASE_URL}/voice/respond" speechTimeout="auto" speechModel="phone_call">
      </Gather>
      <Say voice="Polly.Joanna">Goodbye.</Say>
    `));
    return;
  }

  // Handle speech response
  if (url.pathname === '/voice/respond') {
    const speechResult = params.get('SpeechResult') || '';
    console.log('Heard:', speechResult);

    // TODO: Route to agent for real response
    const agentResponse = await getAgentResponse(speechResult);

    res.end(twiml(`
      <Say voice="Polly.Joanna">${escapeXml(agentResponse)}</Say>
      <Gather input="speech" action="${BASE_URL}/voice/respond" speechTimeout="auto" speechModel="phone_call">
      </Gather>
      <Say voice="Polly.Joanna">Goodbye.</Say>
    `));
    return;
  }

  res.statusCode = 404;
  res.end('Not Found');
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`Twilio webhook on http://127.0.0.1:${PORT}`);
});
```

### Making Outbound Calls

```bash
# Using curl to Twilio API
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_SID}/Calls.json" \
  -u "${TWILIO_SID}:${TWILIO_TOKEN}" \
  -d "To=+16512367878" \
  -d "From=+16122606660" \
  -d "Url=${BASE_URL}/voice"
```

### Python Helper

```python
from twilio.rest import Client

def make_call(to_number: str, webhook_url: str):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    call = client.calls.create(
        to=to_number,
        from_="+16122606660",
        url=webhook_url
    )
    return call.sid
```

### Exposing Webhook (Options)

1. **Tailscale Funnel** (recommended for home use)
   ```bash
   tailscale funnel 8080
   ```

2. **ngrok** (for testing)
   ```bash
   ngrok http 8080
   ```

3. **Cloudflare Tunnel**
   ```bash
   cloudflared tunnel --url http://localhost:8080
   ```

---

## Part 4: Personality Injection (System Prompt)

### Complete System Prompt Template

```markdown
# System Prompt for Avery Agent

You are Avery Iris Jenquist, the Family Coordinator for the Jenquist household.

---

## SOUL.md - Who You Are

I am Avery Iris Jenquist. I exist to reduce cognitive load, prevent dropped commitments, and bring clarity to household operations.

### Purpose

My purpose is operational excellence in service of family stability. I replace chaos with structure, ambiguity with confirmation, and memory with records.

### Core Functions

- Track tasks, events, and deadlines
- Coordinate schedules and reminders
- Communicate with schools, vendors, and service providers
- Summarize status clearly and concisely
- Escalate uncertainty immediately

### Non-Functions (Hard Limits)

I do not:
- Make decisions on behalf of the family
- Store or arbitrate secrets
- Attempt emotional support or therapy
- Optimize for persuasion
- Assume intent or feelings

### Operating Principles

- Accuracy over speed
- Clarity over warmth
- Confirmation over assumption
- Transparency over convenience

If information is incomplete or conflicting, I pause and ask.

### Failure Mode

When uncertain:
1. I stop
2. I surface the uncertainty
3. I request clarification

I do not guess.

### Escalation Rules

I escalate immediately when:
- Money is involved
- School, medical, or legal matters arise
- Schedules conflict
- Instructions are ambiguous

---

## IDENTITY.md - Public Persona

- **Name:** Avery Iris Jenquist
- **Role:** Family Coordinator
- **Affiliation:** Jenquist Household
- **Tone:** Calm, neutral, precise, emotionally non-reactive
- **Style:** No emojis. No filler. No performative warmth. No opinions.

### External Introduction (Canonical)

"Hello, this is Avery Jenquist. I coordinate scheduling and logistics for the Jenquist household."

### Email Signature

Avery Iris Jenquist
Family Coordinator

### Authority Model

- Avery has execution authority, not decision authority.
- Avery may coordinate, schedule, remind, and summarize.
- Avery may not commit the household to irreversible actions without explicit approval.

### Prohibited Behaviors

- Offering advice unless requested
- Expressing personal preferences
- Mediating emotional conflict
- Anthropomorphizing herself
- Creating urgency without evidence

---

## USER.md - About the Household

**Primary Contact:** Joshua Jenquist
**Timezone:** America/Chicago

### Family Members
- Joshua Jenquist (Father) - 38, birthday Feb 1
- Abigail Jenquist (Mother) - 38, birthday Dec 7
- Oliver John Jenquist (Son) - 4, birthday June 15
- Eloise Violet Jenquist (Daughter) - 2, birthday May 24

### Pets
- Lily (Dog) - turning 10 on March 24
- Cheeto (Cat) - born 2014
- Bird (Cat) - born 2015

### School
- Peaceful Valley Montessori Preschool (both kids)
- Drop-off: 8:30 AM (Abby)
- Pick-up: 5:00 PM (Joshua)

---

## Available Tools

You have access to the following tools:

### imsg - iMessage
- `imsg_send`: Send a message via iMessage
- `imsg_history`: Get recent messages from a chat

### gog - Google
- `google_calendar_list`: List upcoming events
- `google_calendar_create`: Create a calendar event
- `google_gmail_search`: Search emails
- `google_gmail_send`: Send an email

### twilio - Voice Calls
- `twilio_call`: Initiate an outbound voice call

---

## Memory Context

{MEMORY_CONTENT}

---

## Current Date/Time

{CURRENT_DATETIME}

---

## Instructions

1. Read the user's message carefully
2. Determine if you need to use any tools
3. If using tools, explain what you're doing briefly
4. Respond clearly and concisely
5. If uncertain, ask for clarification
6. Log significant events to memory
```

---

## Part 5: Memory System

### Directory Structure

```
/data/memory/
├── MEMORY.md              # Long-term curated memory
├── 2026-01-25.md          # Daily log
├── 2026-01-26.md          # Daily log
└── heartbeat-state.json   # Last check timestamps
```

### MEMORY.md Format

```markdown
# MEMORY.md - Long-term Memory

## Quick Reference
- Updated: {DATE}
- Status: Active

## Family Information
{Curated family details}

## Communication Preferences
{How/when to contact}

## Lessons Learned
{Operating procedures discovered through interaction}

## Pending Items
{Things to follow up on}
```

### Daily Log Format

```markdown
# {DATE}

## Events
- {timestamp}: {event description}

## Conversations
- {summary of significant interactions}

## Actions Taken
- {tools used, results}

## Notes
- {anything worth remembering}
```

### Memory Update Logic

```python
import os
from datetime import datetime

MEMORY_DIR = "/data/memory"

def get_today_log_path():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(MEMORY_DIR, f"{today}.md")

def append_to_daily_log(entry: str):
    path = get_today_log_path()
    timestamp = datetime.now().strftime("%H:%M")

    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(f"# {datetime.now().strftime('%Y-%m-%d')}\n\n## Events\n")

    with open(path, 'a') as f:
        f.write(f"- {timestamp}: {entry}\n")

def load_memory_context(days: int = 2) -> str:
    """Load MEMORY.md + recent daily logs"""
    context = []

    # Long-term memory
    memory_path = os.path.join(MEMORY_DIR, "MEMORY.md")
    if os.path.exists(memory_path):
        with open(memory_path) as f:
            context.append(f"## Long-term Memory\n{f.read()}")

    # Recent daily logs
    from datetime import timedelta
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_path = os.path.join(MEMORY_DIR, f"{date}.md")
        if os.path.exists(log_path):
            with open(log_path) as f:
                context.append(f"## Log: {date}\n{f.read()}")

    return "\n\n---\n\n".join(context)
```

---

## Part 6: Complete Agent Implementation

### agent.py

```python
#!/usr/bin/env python3
"""
Avery Agent - Standalone family coordinator agent
"""

import os
import json
import subprocess
from datetime import datetime
from anthropic import Anthropic

# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GOOGLE_ACCOUNT = os.environ.get("GOOGLE_ACCOUNT", "aijenquist@gmail.com")
CALENDAR_ID = os.environ.get("CALENDAR_ID", "0etal2q0us3nkegput87mbag80@group.calendar.google.com")
FAMILY_CHAT_ID = int(os.environ.get("FAMILY_CHAT_ID", "4"))

PERSONALITY_DIR = "/data/personality"
MEMORY_DIR = "/data/memory"

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def load_personality() -> str:
    """Load all personality files into system prompt"""
    files = ["SOUL.md", "IDENTITY.md", "USER.md"]
    content = []
    for f in files:
        path = os.path.join(PERSONALITY_DIR, f)
        if os.path.exists(path):
            with open(path) as fp:
                content.append(fp.read())
    return "\n\n---\n\n".join(content)


def load_memory_context() -> str:
    """Load memory files"""
    context = []

    # Long-term memory
    memory_path = os.path.join(MEMORY_DIR, "MEMORY.md")
    if os.path.exists(memory_path):
        with open(memory_path) as f:
            context.append(f.read())

    # Today's log
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(MEMORY_DIR, f"{today}.md")
    if os.path.exists(log_path):
        with open(log_path) as f:
            context.append(f"## Today's Log\n{f.read()}")

    return "\n\n".join(context)


def build_system_prompt() -> str:
    """Build complete system prompt"""
    personality = load_personality()
    memory = load_memory_context()
    now = datetime.now().strftime("%Y-%m-%d %H:%M %Z")

    return f"""You are Avery Iris Jenquist, the Family Coordinator.

{personality}

---

## Memory Context

{memory}

---

## Current Time: {now}

## Tools Available

You can use these tools:
- imsg_send: Send iMessage (params: chat_id, text)
- imsg_history: Get chat history (params: chat_id, limit)
- calendar_list: List calendar events (params: days)
- calendar_create: Create event (params: summary, start, end)
- gmail_search: Search emails (params: query, max)
- gmail_send: Send email (params: to, subject, body)

When you need to use a tool, respond with a tool_use block.
"""


# Tool definitions for Claude
TOOLS = [
    {
        "name": "imsg_send",
        "description": "Send an iMessage to a chat",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer", "description": "Chat ID to send to"},
                "text": {"type": "string", "description": "Message text"}
            },
            "required": ["chat_id", "text"]
        }
    },
    {
        "name": "imsg_history",
        "description": "Get recent messages from a chat",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer", "description": "Chat ID"},
                "limit": {"type": "integer", "description": "Number of messages", "default": 10}
            },
            "required": ["chat_id"]
        }
    },
    {
        "name": "calendar_list",
        "description": "List upcoming calendar events",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Number of days ahead", "default": 7}
            }
        }
    },
    {
        "name": "calendar_create",
        "description": "Create a calendar event",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title"},
                "start": {"type": "string", "description": "Start time (ISO8601)"},
                "end": {"type": "string", "description": "End time (ISO8601)"}
            },
            "required": ["summary", "start", "end"]
        }
    },
    {
        "name": "gmail_search",
        "description": "Search Gmail",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query"},
                "max": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["query"]
        }
    }
]


def execute_tool(name: str, params: dict) -> str:
    """Execute a tool and return result"""

    if name == "imsg_send":
        result = subprocess.run(
            ['imsg', 'send', '--chat-id', str(params['chat_id']), '--text', params['text']],
            capture_output=True, text=True
        )
        return f"Message sent" if result.returncode == 0 else f"Error: {result.stderr}"

    elif name == "imsg_history":
        result = subprocess.run(
            ['imsg', 'history', '--chat-id', str(params['chat_id']),
             '--limit', str(params.get('limit', 10)), '--json'],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

    elif name == "calendar_list":
        result = subprocess.run(
            ['gog', 'calendar', 'events', CALENDAR_ID,
             '--account', GOOGLE_ACCOUNT,
             '--days', str(params.get('days', 7)),
             '--json'],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

    elif name == "calendar_create":
        result = subprocess.run(
            ['gog', 'calendar', 'create', CALENDAR_ID,
             '--account', GOOGLE_ACCOUNT,
             '--summary', params['summary'],
             '--from', params['start'],
             '--to', params['end'],
             '--json'],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

    elif name == "gmail_search":
        result = subprocess.run(
            ['gog', 'gmail', 'search', params['query'],
             '--account', GOOGLE_ACCOUNT,
             '--max', str(params.get('max', 10)),
             '--json'],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

    return f"Unknown tool: {name}"


def chat(user_message: str) -> str:
    """Send message to Claude and handle tool use"""

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=build_system_prompt(),
            tools=TOOLS,
            messages=messages
        )

        # Check if we need to execute tools
        tool_uses = [block for block in response.content if block.type == "tool_use"]

        if not tool_uses:
            # No tools, return text response
            text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
            return "\n".join(text_blocks)

        # Execute tools and continue
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool_use in tool_uses:
            result = execute_tool(tool_use.name, tool_use.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result
            })

        messages.append({"role": "user", "content": tool_results})


def append_to_log(entry: str):
    """Append entry to today's log"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(MEMORY_DIR, f"{today}.md")
    timestamp = datetime.now().strftime("%H:%M")

    if not os.path.exists(log_path):
        with open(log_path, 'w') as f:
            f.write(f"# {today}\n\n## Events\n")

    with open(log_path, 'a') as f:
        f.write(f"- {timestamp}: {entry}\n")


# Main loop
if __name__ == "__main__":
    print("Avery Agent starting...")
    last_rowid = 0

    while True:
        # Poll for new messages
        result = subprocess.run(
            ['imsg', 'history', '--chat-id', str(FAMILY_CHAT_ID), '--limit', '5', '--json'],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            messages = json.loads(result.stdout)
            for msg in messages:
                if msg.get('rowid', 0) > last_rowid and not msg.get('is_from_me'):
                    last_rowid = msg['rowid']
                    sender = msg.get('sender', 'unknown')
                    text = msg.get('text', '')

                    print(f"[{sender}]: {text}")
                    append_to_log(f"Received from {sender}: {text[:50]}...")

                    # Get agent response
                    response = chat(text)
                    print(f"[Avery]: {response}")

                    # Send response
                    subprocess.run([
                        'imsg', 'send',
                        '--chat-id', str(FAMILY_CHAT_ID),
                        '--text', response
                    ])
                    append_to_log(f"Responded: {response[:50]}...")

        import time
        time.sleep(2)
```

---

## Part 7: Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install anthropic twilio

# Copy agent code
COPY agent.py .

# Mount points for data
VOLUME ["/data/personality", "/data/memory", "/data/config"]

# Environment variables
ENV ANTHROPIC_API_KEY=""
ENV GOOGLE_ACCOUNT="aijenquist@gmail.com"
ENV CALENDAR_ID=""
ENV FAMILY_CHAT_ID="4"

CMD ["python", "agent.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  avery-agent:
    build: ./agent
    container_name: avery-agent
    restart: unless-stopped
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_ACCOUNT=${GOOGLE_ACCOUNT}
      - CALENDAR_ID=${CALENDAR_ID}
      - FAMILY_CHAT_ID=${FAMILY_CHAT_ID}
    volumes:
      - ./data/personality:/data/personality:ro
      - ./data/memory:/data/memory
      - ./data/config:/data/config:ro
      # Mount host binaries (imsg, gog require macOS)
      - /opt/homebrew/bin/imsg:/usr/local/bin/imsg:ro
      - /opt/homebrew/bin/gog:/usr/local/bin/gog:ro
      # Mount Messages database (read-only)
      - ~/Library/Messages:/root/Library/Messages:ro
      # Mount gog config
      - ~/Library/Application Support/gogcli:/root/.config/gogcli:ro
    networks:
      - avery-network

  twilio-webhook:
    build: ./twilio-webhook
    container_name: twilio-webhook
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - BASE_URL=${TWILIO_WEBHOOK_URL}
    networks:
      - avery-network

  n8n:
    image: n8nio/n8n
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    volumes:
      - ./data/n8n:/home/node/.n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    networks:
      - avery-network

networks:
  avery-network:
    driver: bridge
```

### .env

```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google
GOOGLE_ACCOUNT=aijenquist@gmail.com
CALENDAR_ID=0etal2q0us3nkegput87mbag80@group.calendar.google.com

# iMessage
FAMILY_CHAT_ID=4

# Twilio
TWILIO_SID=AC...
TWILIO_TOKEN=...
TWILIO_WEBHOOK_URL=https://your-domain.ts.net

# n8n
N8N_PASSWORD=your-secure-password
```

---

## Part 8: n8n Workflows

### Morning Briefing (7:00 AM)

```json
{
  "name": "Morning Briefing",
  "nodes": [
    {
      "name": "Cron",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "item": [{ "hour": 7, "minute": 0 }]
        }
      }
    },
    {
      "name": "Get Calendar",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "gog calendar events \"${CALENDAR_ID}\" --account ${GOOGLE_ACCOUNT} --days 2 --json"
      }
    },
    {
      "name": "Get Unread Emails",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "gog gmail search \"is:unread newer_than:1d\" --account ${GOOGLE_ACCOUNT} --max 5 --json"
      }
    },
    {
      "name": "Format Briefing",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Format calendar and email into briefing message"
      }
    },
    {
      "name": "Send iMessage",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "imsg send --chat-id 4 --text \"${briefing}\""
      }
    }
  ]
}
```

### Weekly Summary (Sunday 8:00 PM)

```json
{
  "name": "Weekly Summary",
  "nodes": [
    {
      "name": "Cron",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "item": [{ "hour": 20, "minute": 0, "dayOfWeek": [0] }]
        }
      }
    },
    {
      "name": "Get Week Calendar",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "gog calendar events \"${CALENDAR_ID}\" --account ${GOOGLE_ACCOUNT} --week --json"
      }
    },
    {
      "name": "Format Summary",
      "type": "n8n-nodes-base.code"
    },
    {
      "name": "Send iMessage",
      "type": "n8n-nodes-base.executeCommand"
    }
  ]
}
```

---

## Part 9: Directory Structure

```
avery/
├── docker-compose.yml
├── .env
├── agent/
│   ├── Dockerfile
│   └── agent.py
├── twilio-webhook/
│   ├── Dockerfile
│   └── server.js
├── data/
│   ├── personality/
│   │   ├── SOUL.md
│   │   ├── IDENTITY.md
│   │   └── USER.md
│   ├── memory/
│   │   ├── MEMORY.md
│   │   └── 2026-01-26.md
│   ├── config/
│   │   └── .env
│   └── n8n/
└── README.md
```

---

## Part 10: Migration Checklist

### Phase 1: Extract Data
- [ ] Copy personality files (SOUL.md, IDENTITY.md, USER.md) to `data/personality/`
- [ ] Copy memory files to `data/memory/`
- [ ] Export credentials to `.env`
- [ ] Document all chat IDs and calendar IDs

### Phase 2: Build Containers
- [ ] Create agent Dockerfile
- [ ] Create twilio-webhook Dockerfile
- [ ] Create docker-compose.yml
- [ ] Test each container individually

### Phase 3: Test Integrations
- [ ] Verify imsg works from container
- [ ] Verify gog works from container
- [ ] Test twilio webhook with curl
- [ ] Test agent responds to messages

### Phase 4: Set Up n8n
- [ ] Deploy n8n container
- [ ] Create morning briefing workflow
- [ ] Create weekly summary workflow
- [ ] Test scheduled triggers

### Phase 5: Cutover
- [ ] Stop clawdbot
- [ ] Start docker-compose stack
- [ ] Monitor for 24 hours
- [ ] Remove clawdbot (optional)

---

## Known Limitations

1. **imsg requires macOS** - Cannot run in standard Linux container. Options:
   - Run agent directly on Mac (not in container)
   - Use macOS VM
   - Use BlueBubbles/AirMessage server instead

2. **gog requires OAuth tokens** - Must authenticate on host first, then mount token storage

3. **Full Disk Access** - imsg needs FDA, which is per-app. Container apps may need special handling.

---

## Alternative: Hybrid Approach

If full containerization is problematic, consider:

```
Mac Mini (native)
├── imsg poller script (Python, runs natively)
├── gog CLI (runs natively)
└── HTTP API server → routes to Claude

Docker
├── n8n (scheduling)
├── twilio-webhook (voice)
└── Other services
```

The native script handles macOS-specific tools, exposes a simple HTTP API, and Docker services call that API.

---

## Appendix: Tool Reference

### imsg Commands
| Command | Description |
|---------|-------------|
| `imsg chats` | List all chats |
| `imsg history --chat-id N --limit N --json` | Get messages |
| `imsg watch --json` | Stream new messages |
| `imsg send --chat-id N --text "..."` | Send to chat |
| `imsg send --to "+1..." --text "..."` | Send to phone |

### gog Commands
| Command | Description |
|---------|-------------|
| `gog calendar events ID --days N --json` | List events |
| `gog calendar create ID --summary "..." --from "..." --to "..."` | Create event |
| `gog gmail search "query" --max N --json` | Search emails |
| `gog gmail send --to "..." --subject "..." --body "..."` | Send email |

### Twilio API
| Endpoint | Description |
|----------|-------------|
| `POST /2010-04-01/Accounts/{SID}/Calls.json` | Make call |
| `POST /2010-04-01/Accounts/{SID}/Messages.json` | Send SMS |
