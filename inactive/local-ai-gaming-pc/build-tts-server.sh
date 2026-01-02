#!/bin/bash
set -e

echo "Building TTS Inference Server Docker image..."

docker build -t tts-inference-server:latest ./tts-inference-server

echo ""
echo "Build successful!"
echo ""
echo "Next steps:"
echo "1. Create the container (manager will start it on-demand):"
echo "   docker create --name chatterbox-tts --gpus all -v \$(pwd)/voices:/app/voices -v \$(pwd)/cache:/root/.cache/huggingface --network my-network tts-inference-server:latest"
echo ""
echo "2. Test manually:"
echo "   docker start chatterbox-tts"
echo "   curl http://localhost:8006/health"
echo ""
echo "3. Or let the manager handle it - just send a request to:"
echo "   POST http://localhost:8000/v1/audio/speech"
