FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y openssh-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY *.py .
COPY providers/ ./providers/
COPY tools/ ./tools/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "router:app", "--host", "0.0.0.0", "--port", "8000"]
