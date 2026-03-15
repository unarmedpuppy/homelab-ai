#!/usr/bin/env bash
# setup-claude-code.sh
#
# Configure Claude Code settings for local LLM routing on any fleet machine.
# Safely merges required entries into ~/.claude/settings.json without
# overwriting existing config. Idempotent — safe to run repeatedly.
#
# See: docs/adrs/2026-03-15-claude-code-local-routing-optimization.md
#
# Usage:
#   ./scripts/setup-claude-code.sh
#
# After running, add to ~/.bashrc or ~/.zshrc:
#   export HOMELAB_AI_API_KEY="<your-llm-router-key>"
#   alias hal-code='ANTHROPIC_BASE_URL="https://homelab-ai-api.server.unarmedpuppy.com" ANTHROPIC_API_KEY="$HOMELAB_AI_API_KEY" claude'

set -euo pipefail

SETTINGS_FILE="$HOME/.claude/settings.json"

# Ensure directory exists
mkdir -p "$(dirname "$SETTINGS_FILE")"

python3 - <<'PYEOF'
import json
import os
import sys

settings_file = os.path.expanduser("~/.claude/settings.json")

# Load existing settings or start fresh
try:
    with open(settings_file) as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {}
except json.JSONDecodeError as e:
    print(f"WARNING: {settings_file} contains invalid JSON ({e}). Backing up and starting fresh.")
    import shutil
    shutil.copy(settings_file, settings_file + ".bak")
    settings = {}

# Required settings for local LLM routing.
# See: docs/adrs/2026-03-15-claude-code-local-routing-optimization.md
required = {
    # Prevents Claude Code from sending an attribution header that invalidates the KV
    # cache on every request. Without this, each turn re-processes the full system prompt
    # + conversation history — ~90% slower inference on local models.
    # Must be in settings.json (not env var) — env vars arrive too late to suppress the header.
    "CLAUDE_CODE_ATTRIBUTION_HEADER": 0,

    # Reduce outbound traffic to Anthropic servers. Irrelevant when routing locally.
    "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",

    # Max reasoning effort. Local models handle it; don't sandbag on our own hardware.
    "effortLevel": "high",
}

changed = []
for k, v in required.items():
    if settings.get(k) != v:
        settings[k] = v
        changed.append(k)

with open(settings_file, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

if changed:
    print(f"Updated {settings_file}:")
    for k in changed:
        print(f"  + {k} = {required[k]!r}")
else:
    print(f"{settings_file} is already up to date.")
PYEOF

echo ""
echo "To route Claude Code through the local llm-router, add to ~/.bashrc or ~/.zshrc:"
echo ""
echo '  export HOMELAB_AI_API_KEY="<your-llm-router-key>"'
echo '  alias hal-code='"'"'ANTHROPIC_BASE_URL="https://homelab-ai-api.server.unarmedpuppy.com" ANTHROPIC_API_KEY="$HOMELAB_AI_API_KEY" claude'"'"
echo ""
echo "Then run: hal-code"
echo "Routing chain: gaming-pc (qwen3.5-27b) -> zai (glm-5) -> claude-harness (Anthropic)"
