# Claude Code Harness - Containerized
#
# OpenAI-compatible API wrapper for Claude Code CLI.
# Requires OAuth tokens mounted from host (~/.claude.json, ~/.claude/)

FROM python:3.11-slim

# Install Node.js (required for Claude Code CLI)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Create app user with specific UID to match host user (for OAuth token access)
# This allows the container to read/write ~/.claude.json mounted from host
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -m -u ${USER_ID} -g appuser appuser

# Set up working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create directories for Claude credentials (will be mounted)
RUN mkdir -p /home/appuser/.claude && \
    chown -R appuser:appuser /home/appuser

# Switch to app user
USER appuser

# Set HOME for Claude CLI to find credentials
ENV HOME=/home/appuser

# Expose port
EXPOSE 8013

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8013/health || exit 1

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]
