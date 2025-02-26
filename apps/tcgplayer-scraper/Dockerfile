# Use Python as base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0=2.50.3-2 \
    libnss3=2:3.26.2-1.1+deb9u1 \
    libgconf-2-4=3.2.6-4+b1 \
    libfontconfig1=2.11.0-6.7+b1 \
    wget \
    unzip \
    curl \
    chromium \
    chromium-browser \
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
