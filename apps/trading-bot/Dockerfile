# Multi-stage Dockerfile for Trading Bot API
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements/base.txt requirements/development.txt ./
RUN pip install --upgrade pip && \
    pip install -r base.txt && \
    playwright install chromium && \
    playwright install-deps chromium

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install runtime dependencies (including Playwright browser deps)
RUN apt-get update && apt-get install -y \
    curl \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy Playwright browsers from builder stage
COPY --from=builder /root/.cache/ms-playwright /ms-playwright

# Create non-root user
RUN groupadd -r tradingbot && useradd -r -g tradingbot tradingbot

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY main.py pytest.ini ./
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Create necessary directories
RUN mkdir -p /app/data /app/logs && \
    chown -R tradingbot:tradingbot /app

# Switch to non-root user
USER tradingbot

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]
