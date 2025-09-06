FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY scraper.py ./
# .env is provided via env_file in compose; not copied into the image
VOLUME ["/app/data"]
CMD ["python", "scraper.py"]
