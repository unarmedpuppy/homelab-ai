# Bird Bookmark Processor
# Node.js for Bird CLI + Python for processing
FROM harbor.server.unarmedpuppy.com/docker-hub/library/node:22-alpine

# Install Python and git
RUN apk add --no-cache python3 py3-pip git bash curl

# Install Bird CLI globally
RUN npm install -g @steipete/bird

# Create app directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Default command runs the processor
CMD ["python3", "process_bookmarks.py"]
