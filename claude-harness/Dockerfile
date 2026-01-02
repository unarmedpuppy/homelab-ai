# Claude Code Harness - Containerized
#
# OpenAI-compatible API wrapper for Claude Code CLI.
# OAuth tokens stored in Docker volume (claude-credentials).
#
# First-time setup:
#   docker exec -it claude-harness claude
#   (Follow OAuth flow in browser, tokens persist in volume)

FROM python:3.11-slim

# Install Node.js, Git, and SSH client
RUN apt-get update && apt-get install -y \
    curl \
    git \
    openssh-client \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Create non-root user for security
RUN useradd -m -s /bin/bash appuser

# Set up working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and entrypoint
COPY main.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Create credentials directory (will be a volume mount point)
RUN mkdir -p /home/appuser/.claude && \
    chown -R appuser:appuser /home/appuser /app

# Switch to app user
USER appuser

# Set HOME for Claude CLI to find credentials
ENV HOME=/home/appuser

# Expose port
EXPOSE 8013

# Health check - allow longer start period for first-time auth
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8013/health || exit 1

# Use entrypoint script to check for auth before starting
ENTRYPOINT ["/app/entrypoint.sh"]
