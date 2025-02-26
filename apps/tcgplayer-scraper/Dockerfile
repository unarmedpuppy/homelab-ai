# Use Python as base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    chromium \
    chromium-driver

# Install Python dependencies
COPY app/ /app
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Selenium & Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Expose Flask's default port
EXPOSE 5000

# Command to start the Flask app
CMD ["python", "tcg.py"]
