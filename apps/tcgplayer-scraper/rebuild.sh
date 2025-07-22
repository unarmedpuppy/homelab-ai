#!/bin/bash

echo "Rebuilding and restarting TCGPlayer scraper..."

# Stop existing container
docker-compose down

# Remove old images to force rebuild
docker-compose build --no-cache

# Start the container
docker-compose up -d

echo "Container started. Check logs with: docker-compose logs -f"
echo "Test the web interface at: http://localhost:5000" 