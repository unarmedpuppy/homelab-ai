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

# Install Chromium dependencies for Puppeteer MCP (optional, on-demand)
# Using chromium instead of chrome for smaller image size
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Puppeteer to use system Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Install code-server for browser-based VS Code
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Configure SSH server - key-only auth, allow appuser
RUN sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    echo "AllowUsers appuser" >> /etc/ssh/sshd_config

# Install Claude Code CLI globally via npm
# IMPORTANT: Do NOT use the native installer (curl https://claude.ai/install.sh | bash)
# - npm installs to /usr/bin/claude (works with yolo wrapper)
# - Native installer installs to ~/.local/bin/claude (breaks yolo wrapper paths)
# - npm update runs on container start via entrypoint.sh for auto-updates
RUN npm install -g @anthropic-ai/claude-code

# Install Puppeteer MCP server (on-demand browser automation)
# Enable with: mcp-puppeteer enable
# Disable with: mcp-puppeteer disable
RUN npm install -g @anthropic-ai/mcp-server-puppeteer

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
COPY mcp-puppeteer.sh /usr/local/bin/mcp-puppeteer
RUN chmod +x entrypoint.sh ralph-wiggum.sh /usr/local/bin/mcp-puppeteer

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
