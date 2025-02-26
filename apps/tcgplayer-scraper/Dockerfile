# Use an official Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0

# Ensure permissions
RUN chmod +x /usr/bin/chromedriver

# Install Python dependencies
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Expose Flask's default port
EXPOSE 5000

# Command to start the Flask app
CMD ["python", "tcg.py"]
