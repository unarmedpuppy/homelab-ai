# Memori Setup Guide

## Quick Setup

### Step 1: Install Memori

Choose one of these options:

**Option A: User Installation (Recommended for macOS)**
```bash
python3 -m pip install --user memori
```

**Option B: Virtual Environment**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Memori
pip install memori
```

**Option C: Add to Project Requirements**
```bash
# Add to requirements.txt
echo "memori>=2.1.1" >> requirements.txt
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required: OpenAI API Key
export MEMORI_AGENTS__OPENAI_API_KEY="sk-..."

# Optional: PostgreSQL (defaults to SQLite)
export MEMORI_DATABASE__CONNECTION_STRING="postgresql://user:pass@localhost/memori"

# Optional: Namespace (defaults to "home-server")
export MEMORI_MEMORY__NAMESPACE="home-server"
```

### Step 3: Run Setup Script

```bash
python3 apps/agent_memory/setup.py
```

### Step 4: Test Installation

```bash
python3 apps/agent_memory/test_memori.py
```

## Database Options

### SQLite (Default - Easiest)

No configuration needed! Memori will create `agent_memory.db` automatically.

### PostgreSQL (Recommended for Production)

1. **Create Database**:
   ```sql
   CREATE DATABASE memori;
   ```

2. **Set Connection String**:
   ```bash
   export MEMORI_DATABASE__CONNECTION_STRING="postgresql://user:pass@localhost/memori"
   ```

3. **Memori will create tables automatically** on first use.

## Usage

### Basic Usage

```python
from apps.agent_memory import setup_memori

# Enable memory (one time, at startup)
memori = setup_memori()

# That's it! Memory is now active
# All LLM calls are automatically intercepted
```

### With OpenAI

```python
from openai import OpenAI
from apps.agent_memory import setup_memori

# Setup memory
memori = setup_memori()

# Use OpenAI normally - Memori intercepts automatically
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Help me deploy a service"}]
)
# Context is automatically injected
# Conversation is automatically recorded
```

### With Other LLMs

Memori works with any LLM through LiteLLM:

```python
from litellm import completion
from apps.agent_memory import setup_memori

memori = setup_memori()

# Works with any LiteLLM-compatible provider
response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Verification

### Check if Memory is Working

1. **Make an LLM call** (with Memori enabled)
2. **Make another call** with related context
3. **Check if context is injected** (Memori logs to console)

### Test Script

Run the test script:

```bash
python3 apps/agent_memory/test_memori.py
```

## Troubleshooting

### "Memori is not installed"

**Solution**: Install Memori (see Step 1 above)

### "OpenAI API key not found"

**Solution**: Set `MEMORI_AGENTS__OPENAI_API_KEY` environment variable

### "Database connection failed"

**Solution**: 
- Check database connection string
- Verify database exists (for PostgreSQL)
- Check database permissions

### "Memory not working"

**Solution**:
1. Verify `memori.enable()` was called
2. Check console logs for errors
3. Verify database connection
4. Check API key is set

## Next Steps

After setup:

1. **Update Agent Prompts**: Add memory section (see `SERVER_AGENT_PROMPT.md`)
2. **Test with Real Workflow**: Use with actual agent tasks
3. **Monitor Memory**: Check database for stored memories
4. **Review Patterns**: Conscious Agent learns patterns automatically

## References

- **Memori GitHub**: https://github.com/GibsonAI/Memori
- **Memori Docs**: https://gibsonai.github.io/memori/
- **Comparison**: `apps/docs/MEMORY_SYSTEM_COMPARISON.md`
- **Integration Guide**: `apps/agent_memory/README.md`

---

**Status**: Ready to use after installation
**Priority**: High
**Effort**: Low (just install and enable!)

