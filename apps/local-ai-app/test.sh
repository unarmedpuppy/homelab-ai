#!/bin/bash

# Test script for local-ai-app
# This script tests the connection to your Windows AI service

echo "Testing Local AI App..."

# Get the service URL (adjust if using different domain)
SERVICE_URL="http://localhost:8001"
if [ ! -z "$1" ]; then
    SERVICE_URL="$1"
fi

echo "Testing service at: $SERVICE_URL"

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s "$SERVICE_URL/health" | jq '.' || echo "Health check failed"

echo -e "\n2. Testing models endpoint..."
curl -s "$SERVICE_URL/v1/models" | jq '.' || echo "Models check failed"

echo -e "\n3. Testing model info endpoint..."
curl -s "$SERVICE_URL/models/info" | jq '.' || echo "Model info check failed"

echo -e "\n4. Testing usage stats..."
curl -s "$SERVICE_URL/usage/stats" | jq '.' || echo "Usage stats check failed"

echo -e "\n5. Testing API docs..."
curl -s "$SERVICE_URL/docs" | jq '.' || echo "API docs check failed"

echo -e "\n6. Testing comprehensive status..."
curl -s "$SERVICE_URL/status" | jq '.' || echo "Status check failed"

echo -e "\n7. Testing chat completion..."
curl -s -X POST "$SERVICE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3-8b",
    "messages": [{"role": "user", "content": "Say hello in one word."}],
    "max_tokens": 10
  }' | jq '.' || echo "Chat completion failed"

echo -e "\nTest complete!"
