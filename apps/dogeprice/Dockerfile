FROM python:3.9-slim

# Install system dependencies and Google Chrome
RUN apt-get update && apt-get install -y wget gnupg2 unzip curl \
 && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
 && apt-get update \
 && apt-get install -y google-chrome-stable

# Set ChromeDriver version known to support Chrome 134
ENV CHROMEDRIVER_VERSION=134.0.7070.0
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip \
 && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
 && rm /tmp/chromedriver.zip \
 && chmod +x /usr/local/bin/chromedriver

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
