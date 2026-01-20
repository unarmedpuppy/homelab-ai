# Claude Code Harness - Containerized
#
# OpenAI-compatible API wrapper for Claude Code CLI.
# OAuth tokens stored in Docker volume (claude-credentials).
# Built via GitHub Actions CI/CD - see .github/workflows/build-and-push.yml
#
# First-time setup:
#   docker exec -it claude-harness claude
#   (Follow OAuth flow in browser, tokens persist in volume)

FROM python:3.11-slim

# Install Node.js, Git, SSH (client + server), tmux, and gosu for privilege dropping
RUN apt-get update && apt-get install -y \
    curl \
    git \
    openssh-client \
    openssh-server \
    tmux \
    gosu \
    jq \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd

# Install code-server for browser-based VS Code
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Configure SSH server - key-only auth, allow appuser
RUN sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    echo "AllowUsers appuser" >> /etc/ssh/sshd_config

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Create non-root user for security
RUN useradd -m -s /bin/bash appuser

# Set up working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code, entrypoint, and scripts
COPY main.py .
COPY entrypoint.sh .
COPY ralph-wiggum.sh .
RUN chmod +x entrypoint.sh ralph-wiggum.sh

# Copy Claude Code configuration (CLAUDE.md and skills)
COPY CLAUDE.md .
COPY .claude/ .claude/

# Create directories (volumes will be mounted at runtime)
RUN mkdir -p /home/appuser/.claude /home/appuser/.ssh /workspace && \
    chown -R appuser:appuser /home/appuser /app /workspace

# Stay as root - entrypoint will fix volume permissions then drop to appuser
ENV HOME=/home/appuser
ENV APPUSER=appuser

# Expose ports (API, SSH, and code-server)
EXPOSE 8013 22 8443

# Health check - allow longer start period for first-time auth
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8013/health || exit 1

# Use entrypoint script to check for auth before starting
ENTRYPOINT ["/app/entrypoint.sh"]
