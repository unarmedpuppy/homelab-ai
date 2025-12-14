# Local Jobin Agent - Implementation Plan

**Created**: 2025-12-13
**Target**: Home server with RTX 3090 (24GB VRAM)
**Status**: Planning

---

## Overview

Deploy Jobin as a locally-running AI agent on your home server, using an open-source LLM for privacy and on-demand availability.

---

## Recommended Model Stack

### Primary: Qwen2.5-32B-Instruct (Q4_K_M)
- **VRAM**: ~20GB
- **Why**: Best balance of capability and speed for Jobin's tasks
- **Strengths**: Excellent instruction following, structured output, markdown generation

### Fast Mode: Qwen2.5-14B-Instruct (Q6_K)
- **VRAM**: ~12GB
- **Why**: Quick responses for simple daily input processing
- **Use when**: Quick logging, single-item updates

### Optional Heavy Mode: Llama-3.3-70B (Q3_K_M)
- **VRAM**: ~24GB (tight fit)
- **Why**: Complex briefings, multi-file synthesis
- **Use when**: Weekly summaries, goal reviews

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Server (RTX 3090)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌──────────────────────────────────┐  │
│  │   Ollama    │────▶│     Qwen2.5-32B-Instruct         │  │
│  │   Server    │     │     (GPU accelerated)            │  │
│  └──────┬──────┘     └──────────────────────────────────┘  │
│         │                                                   │
│         │ API (localhost:11434)                             │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Jobin Agent Service                      │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  System Prompt (jobin.md + context loader)     │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────────┐   │  │
│  │  │  Tools   │ │ File I/O │ │ Template Engine    │   │  │
│  │  └──────────┘ └──────────┘ └────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Life OS Repository                       │  │
│  │  /path/to/life-os/data/                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         │ Interfaces (pick one or more)
         ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   Telegram     │  │   Web UI       │  │   CLI          │
│   Bot          │  │   (optional)   │  │   (direct)     │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## Implementation Phases

### Phase 1: Model Setup (Ollama)

```bash
# Install Ollama (if not already)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the recommended model
ollama pull qwen2.5:32b-instruct-q4_K_M

# Verify GPU acceleration
ollama run qwen2.5:32b-instruct-q4_K_M "Say hello"

# Check VRAM usage
nvidia-smi
```

**Ollama config** (`~/.ollama/config.json` or environment):
```json
{
  "gpu_memory_fraction": 0.95,
  "num_ctx": 8192,
  "num_gpu": 99
}
```

### Phase 2: Jobin Agent Core

Create a Python-based agent that wraps the LLM with Life OS context.

**File structure:**
```
life-os/
└── agents/
    └── local-jobin/
        ├── jobin_agent.py       # Main agent logic
        ├── context_loader.py    # Loads relevant files for context
        ├── file_tools.py        # Read/write life-os files
        ├── templates.py         # Template handling
        ├── config.yaml          # Configuration
        ├── requirements.txt     # Dependencies
        └── Dockerfile           # Container deployment
```

**Core components:**

#### 2.1 Context Loader (`context_loader.py`)

Dynamically loads relevant context based on the task:

```python
"""
Context loader for Jobin agent.
Loads relevant Life OS files based on task type.
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
import yaml

class ContextLoader:
    def __init__(self, life_os_path: str):
        self.base = Path(life_os_path) / "data"

    def load_persona(self) -> str:
        """Load Jobin's persona definition."""
        persona_path = self.base.parent / "agents/personas/jobin.md"
        return persona_path.read_text()

    def load_biography_context(self) -> str:
        """Load quick facts about Joshua."""
        overview = self.base / "biography/overview.md"
        return overview.read_text() if overview.exists() else ""

    def load_recent_journal(self, days: int = 3) -> list[str]:
        """Load recent journal entries for context."""
        entries = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            path = self.base / f"journal/{date.year}/{date.month:02d}/{date.strftime('%Y-%m-%d')}.md"
            if path.exists():
                entries.append(path.read_text())
        return entries

    def load_active_todos(self) -> str:
        """Load current todo list."""
        todos = self.base / "todos/active.md"
        return todos.read_text() if todos.exists() else ""

    def load_family_context(self) -> list[str]:
        """Load family contact files for relationship context."""
        family_dir = self.base / "people/family"
        return [f.read_text() for f in family_dir.glob("*.md") if not f.name.startswith("_")]

    def get_context_for_task(self, task_type: str) -> str:
        """Build context string based on task type."""
        context_parts = [self.load_persona()]

        if task_type in ["daily_input", "evening_review"]:
            context_parts.append("## Recent Journal Entries\n")
            context_parts.extend(self.load_recent_journal(2))
            context_parts.append("## Active Todos\n" + self.load_active_todos())

        elif task_type == "morning_briefing":
            context_parts.append("## Biography Context\n" + self.load_biography_context())
            context_parts.append("## Family Context\n")
            context_parts.extend(self.load_family_context())
            context_parts.append("## Active Todos\n" + self.load_active_todos())

        elif task_type == "contact_update":
            context_parts.append("## Family Context\n")
            context_parts.extend(self.load_family_context())

        return "\n\n---\n\n".join(context_parts)
```

#### 2.2 File Tools (`file_tools.py`)

Safe file operations for the agent:

```python
"""
File tools for Jobin agent.
Provides safe read/write operations to Life OS.
"""
from pathlib import Path
from datetime import datetime
import yaml
import re

class LifeOSFiles:
    def __init__(self, life_os_path: str):
        self.base = Path(life_os_path) / "data"
        self.templates = {
            "journal": self.base / "journal/templates/daily.md",
            "contact": self.base / "people/templates/contact.md",
            "event": self.base / "events/templates/event.md",
        }

    def read_file(self, relative_path: str) -> str:
        """Read a file from life-os/data/"""
        path = self.base / relative_path
        if not path.exists():
            return f"File not found: {relative_path}"
        return path.read_text()

    def write_file(self, relative_path: str, content: str) -> str:
        """Write a file to life-os/data/"""
        path = self.base / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Written: {relative_path}"

    def append_to_file(self, relative_path: str, content: str) -> str:
        """Append content to an existing file."""
        path = self.base / relative_path
        if not path.exists():
            return f"File not found: {relative_path}"
        existing = path.read_text()
        path.write_text(existing + "\n" + content)
        return f"Appended to: {relative_path}"

    def get_or_create_journal(self, date: datetime = None) -> tuple[str, str]:
        """Get today's journal, creating from template if needed."""
        date = date or datetime.now()
        rel_path = f"journal/{date.year}/{date.month:02d}/{date.strftime('%Y-%m-%d')}.md"
        path = self.base / rel_path

        if path.exists():
            return rel_path, path.read_text()

        # Create from template
        template = self.templates["journal"].read_text()
        content = template.replace("{{DATE}}", date.strftime("%Y-%m-%d"))
        content = content.replace("{{DAY_NAME}}", date.strftime("%A"))
        content = content.replace("{{MONTH}}", date.strftime("%B"))
        content = content.replace("{{DAY}}", str(date.day))
        content = content.replace("{{YEAR}}", str(date.year))

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return rel_path, content

    def update_contact_last_seen(self, contact_path: str) -> str:
        """Update a contact's last_contact field."""
        path = self.base / contact_path
        if not path.exists():
            return f"Contact not found: {contact_path}"

        content = path.read_text()
        today = datetime.now().strftime("%Y-%m-%d")

        # Update YAML frontmatter
        if "last_contact:" in content:
            content = re.sub(
                r"last_contact:.*",
                f"last_contact: {today}",
                content
            )

        path.write_text(content)
        return f"Updated last_contact for {contact_path}"

    def list_contacts(self, category: str = None) -> list[str]:
        """List all contacts, optionally filtered by category."""
        contacts = []
        search_path = self.base / "people"
        if category:
            search_path = search_path / category

        for f in search_path.rglob("*.md"):
            if not f.name.startswith("_") and "template" not in f.name:
                contacts.append(str(f.relative_to(self.base)))
        return contacts
```

#### 2.3 Main Agent (`jobin_agent.py`)

```python
"""
Jobin Agent - Local Life OS Assistant

Runs on home server with RTX 3090, uses Ollama for inference.
"""
import os
import json
from datetime import datetime
from ollama import Client
from context_loader import ContextLoader
from file_tools import LifeOSFiles

class JobinAgent:
    def __init__(
        self,
        life_os_path: str,
        model: str = "qwen2.5:32b-instruct-q4_K_M",
        ollama_host: str = "http://localhost:11434"
    ):
        self.model = model
        self.client = Client(host=ollama_host)
        self.context = ContextLoader(life_os_path)
        self.files = LifeOSFiles(life_os_path)

        # Tool definitions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file from Life OS data directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative path from data/"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file in Life OS",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "append_to_journal",
                    "description": "Append content to today's journal entry",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "string", "enum": ["interactions", "accomplishments", "reflections", "tomorrow"]},
                            "content": {"type": "string"}
                        },
                        "required": ["section", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_contact",
                    "description": "Update a contact's last_contact date and optionally add notes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contact_path": {"type": "string"},
                            "note": {"type": "string", "description": "Optional note to add to interaction history"}
                        },
                        "required": ["contact_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_contacts",
                    "description": "List all contacts, optionally by category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": ["family", "friends", "professional", "community"]}
                        }
                    }
                }
            }
        ]

    def execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool and return the result."""
        if name == "read_file":
            return self.files.read_file(args["path"])
        elif name == "write_file":
            return self.files.write_file(args["path"], args["content"])
        elif name == "append_to_journal":
            journal_path, _ = self.files.get_or_create_journal()
            return self.files.append_to_file(journal_path, f"\n### {args['section'].title()}\n{args['content']}")
        elif name == "update_contact":
            result = self.files.update_contact_last_seen(args["contact_path"])
            if "note" in args:
                # Add note to interaction history
                self.files.append_to_file(
                    args["contact_path"],
                    f"- [{datetime.now().strftime('%Y-%m-%d')}] {args['note']}"
                )
            return result
        elif name == "list_contacts":
            return json.dumps(self.files.list_contacts(args.get("category")))
        return f"Unknown tool: {name}"

    def chat(self, user_message: str, task_type: str = "daily_input") -> str:
        """
        Process a user message with Jobin.

        Args:
            user_message: The user's input
            task_type: One of "daily_input", "morning_briefing", "evening_review", "contact_update"
        """
        # Build context-aware system prompt
        system_prompt = self.context.get_context_for_task(task_type)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # Initial response
        response = self.client.chat(
            model=self.model,
            messages=messages,
            tools=self.tools
        )

        # Handle tool calls in a loop
        while response.message.tool_calls:
            # Add assistant message with tool calls
            messages.append(response.message)

            # Execute each tool and add results
            for tool_call in response.message.tool_calls:
                result = self.execute_tool(
                    tool_call.function.name,
                    tool_call.function.arguments
                )
                messages.append({
                    "role": "tool",
                    "content": result
                })

            # Get next response
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=self.tools
            )

        return response.message.content

    def morning_briefing(self) -> str:
        """Generate a morning briefing."""
        return self.chat(
            "Generate my morning briefing for today. Include schedule, upcoming birthdays, goal check-ins, and anything I should remember.",
            task_type="morning_briefing"
        )

    def process_daily_input(self, input_text: str) -> str:
        """Process a daily input dump."""
        return self.chat(
            f"Process this daily input and update the relevant files:\n\n{input_text}",
            task_type="daily_input"
        )


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Jobin - Life OS Assistant")
    parser.add_argument("--path", default="/path/to/life-os", help="Path to life-os repo")
    parser.add_argument("--model", default="qwen2.5:32b-instruct-q4_K_M")
    parser.add_argument("--mode", choices=["chat", "briefing", "process"], default="chat")
    parser.add_argument("message", nargs="?", help="Message for chat/process mode")

    args = parser.parse_args()

    jobin = JobinAgent(args.path, args.model)

    if args.mode == "briefing":
        print(jobin.morning_briefing())
    elif args.mode == "process":
        print(jobin.process_daily_input(args.message))
    else:
        # Interactive chat
        print("Jobin: Hey! What's on your mind?")
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("Jobin: Take care! 👋")
                    break
                response = jobin.chat(user_input)
                print(f"\nJobin: {response}")
            except KeyboardInterrupt:
                print("\nJobin: Bye!")
                break
```

#### 2.4 Requirements (`requirements.txt`)

```
ollama>=0.3.0
pyyaml>=6.0
python-dateutil>=2.8.0
```

### Phase 3: Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY config.yaml .

# Life OS repo mounted at runtime
VOLUME /life-os

ENV LIFE_OS_PATH=/life-os
ENV OLLAMA_HOST=http://host.docker.internal:11434

CMD ["python", "jobin_agent.py", "--path", "/life-os"]
```

**docker-compose.yaml:**
```yaml
version: '3.8'

services:
  jobin:
    build: .
    container_name: jobin-agent
    volumes:
      - /path/to/life-os:/life-os
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - LIFE_OS_PATH=/life-os
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

volumes:
  ollama_data:
```

### Phase 4: Interface Options

#### Option A: Telegram Bot (Recommended)

```python
"""
Telegram interface for Jobin.
Add to jobin_agent.py or as separate service.
"""
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

class JobinTelegramBot:
    def __init__(self, jobin: JobinAgent, token: str):
        self.jobin = jobin
        self.app = Application.builder().token(token).build()

        # Handlers
        self.app.add_handler(CommandHandler("briefing", self.briefing))
        self.app.add_handler(CommandHandler("process", self.process))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat))

    async def briefing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate morning briefing."""
        await update.message.reply_text("Generating your briefing...")
        response = self.jobin.morning_briefing()
        await update.message.reply_text(response)

    async def process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process daily input."""
        text = " ".join(context.args)
        response = self.jobin.process_daily_input(text)
        await update.message.reply_text(response)

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """General chat."""
        response = self.jobin.chat(update.message.text)
        await update.message.reply_text(response)

    def run(self):
        self.app.run_polling()
```

#### Option B: n8n Webhook Integration

Create an n8n workflow that:
1. Receives webhook from Telegram/Discord/SMS gateway
2. Calls Jobin API endpoint
3. Returns response to user

**Jobin HTTP API wrapper:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
jobin = JobinAgent("/path/to/life-os")

class ChatRequest(BaseModel):
    message: str
    task_type: str = "daily_input"

@app.post("/chat")
def chat(req: ChatRequest):
    return {"response": jobin.chat(req.message, req.task_type)}

@app.get("/briefing")
def briefing():
    return {"response": jobin.morning_briefing()}
```

#### Option C: CLI with tmux

Simple but effective - run in a persistent tmux session:

```bash
# Create persistent session
tmux new-session -d -s jobin

# Attach and run
tmux attach -t jobin
python jobin_agent.py --path /path/to/life-os
```

---

## Configuration (`config.yaml`)

```yaml
# Jobin Agent Configuration

life_os_path: /path/to/life-os

models:
  default: qwen2.5:32b-instruct-q4_K_M
  fast: qwen2.5:14b-instruct-q6_K
  heavy: llama3.3:70b-instruct-q3_K_M

ollama:
  host: http://localhost:11434
  context_length: 8192

context:
  # Days of journal history to include
  journal_lookback: 3
  # Include family contacts in all contexts
  always_include_family: true
  # Max tokens for context
  max_context_tokens: 4000

telegram:
  token: ${TELEGRAM_BOT_TOKEN}
  allowed_users:
    - your_telegram_id

logging:
  level: INFO
  file: /var/log/jobin/agent.log
```

---

## Startup Script

**`/usr/local/bin/jobin`:**
```bash
#!/bin/bash

LIFE_OS_PATH="${LIFE_OS_PATH:-/path/to/life-os}"
MODEL="${JOBIN_MODEL:-qwen2.5:32b-instruct-q4_K_M}"

case "$1" in
  start)
    docker-compose -f $LIFE_OS_PATH/agents/local-jobin/docker-compose.yaml up -d
    ;;
  stop)
    docker-compose -f $LIFE_OS_PATH/agents/local-jobin/docker-compose.yaml down
    ;;
  chat)
    shift
    python3 $LIFE_OS_PATH/agents/local-jobin/jobin_agent.py --path $LIFE_OS_PATH --mode chat "$@"
    ;;
  briefing)
    python3 $LIFE_OS_PATH/agents/local-jobin/jobin_agent.py --path $LIFE_OS_PATH --mode briefing
    ;;
  process)
    shift
    python3 $LIFE_OS_PATH/agents/local-jobin/jobin_agent.py --path $LIFE_OS_PATH --mode process "$@"
    ;;
  *)
    echo "Usage: jobin {start|stop|chat|briefing|process}"
    exit 1
    ;;
esac
```

---

## Performance Tuning

### Ollama Settings for RTX 3090

```bash
# Set in environment or ollama config
export OLLAMA_NUM_PARALLEL=2      # Allow 2 concurrent requests
export OLLAMA_MAX_LOADED_MODELS=1 # Only one model in VRAM
export OLLAMA_FLASH_ATTENTION=1   # Enable flash attention
```

### Context Window Optimization

For 32B model on 24GB VRAM:
- **Safe**: 4096 tokens context
- **Moderate**: 8192 tokens context (recommended)
- **Aggressive**: 16384 tokens context (may require offloading)

---

## Testing Checklist

- [ ] Ollama runs with GPU acceleration (`nvidia-smi` shows usage)
- [ ] Model loads within VRAM (no swap/offload)
- [ ] Context loader finds all life-os paths correctly
- [ ] File tools can read/write without errors
- [ ] Tool calling works (model calls functions)
- [ ] Journal creation from template works
- [ ] Contact updates work
- [ ] Morning briefing generates useful output
- [ ] Daily input processing works end-to-end
- [ ] Telegram bot responds (if using)

---

## Future Enhancements

1. **Memory/RAG**: Add vector store for semantic search across all life-os content
2. **Calendar Integration**: Pull Google Calendar via n8n for schedule awareness
3. **Voice Interface**: Whisper for voice input, TTS for responses
4. **Mobile App**: Simple React Native app that talks to Jobin API
5. **Auto-commit**: Have Jobin commit changes to git after processing

---

## Quick Start Summary

```bash
# 1. Install Ollama and pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:32b-instruct-q4_K_M

# 2. Clone and setup
cd /path/to/life-os/agents
mkdir -p local-jobin && cd local-jobin
# Copy the files from this plan

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test it
python jobin_agent.py --path /path/to/life-os --mode briefing

# 5. Deploy
docker-compose up -d
```

---

## Related Documents

- [jobin.md](../personas/jobin.md) - Jobin persona definition
- [overview.md](life-os/overview.md) - Life OS architecture
- [phase-3-automation.md](life-os/phase-3-automation.md) - n8n integration plans
