#!/bin/bash
set -e

# Load HF_TOKEN from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HF_TOKEN not set. Either:"
    echo "  1. Create a .env file with: HF_TOKEN=hf_your_token"
    echo "  2. Or run: HF_TOKEN=hf_xxx ./setup-tts-container.sh"
    exit 1
fi

echo "Removing existing chatterbox-tts container (if any)..."
docker rm -f chatterbox-tts 2>/dev/null || true

echo "Creating chatterbox-tts container..."
docker create --name chatterbox-tts --gpus all \
  -e HF_TOKEN="$HF_TOKEN" \
  -v $(pwd)/voices:/app/voices \
  -v $(pwd)/cache:/root/.cache/huggingface \
  --network my-network \
  tts-inference-server:latest

echo ""
echo "Container created successfully!"
echo "The manager will start it on-demand or you can start manually:"
echo "  docker start chatterbox-tts"
