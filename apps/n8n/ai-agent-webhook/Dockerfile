FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webhook_service.py .

# Create events directory
RUN mkdir -p /app/events

EXPOSE 8080

CMD ["python", "webhook_service.py"]

