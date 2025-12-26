FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir discord.py

COPY bot.py .

CMD ["python", "-u", "bot.py"]
