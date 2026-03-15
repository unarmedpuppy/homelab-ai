# Dockerfile for eval-runner service
# No GPU needed — this service calls the llm-router, it doesn't run models

FROM harbor.server.unarmedpuppy.com/docker-hub/library/python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY cases/ ./cases/
COPY suites/ ./suites/

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8020

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8020/health || exit 1

CMD ["uvicorn", "eval_runner:app", "--host", "0.0.0.0", "--port", "8020"]
