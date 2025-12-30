FROM harbor.server.unarmedpuppy.com/docker-hub/library/python:3.11-slim

WORKDIR /app

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY tayne_persona.py .
COPY bot.py .

CMD ["python", "-u", "bot.py"]
