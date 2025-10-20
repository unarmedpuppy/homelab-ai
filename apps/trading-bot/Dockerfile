# syntax=docker/dockerfile:1
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ibkr_uw_sma_bot.py /app/ibkr_uw_sma_bot.py
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=10 CMD curl -fsS http://localhost:8000/ || exit 1
CMD ["uvicorn","ibkr_uw_sma_bot:app","--host","0.0.0.0","--port","8000"]
