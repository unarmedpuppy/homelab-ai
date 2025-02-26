# Use Python as base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    chromium \
    chromium-driver

# Ensure Chromedriver has correct permissions
RUN chmod +x /usr/bin/chromedriver

# Install Python dependencies
COPY app/ /app
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Expose Flask's default port
EXPOSE 5000

# Command to start the Flask app
CMD ["python", "tcg.py"]
