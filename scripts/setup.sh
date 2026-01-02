#!/bin/bash

# Setup script for local AI vLLM containers
# This script creates the model containers (stopped by default)

echo "Setting up local AI vLLM containers..."

# Create directories
mkdir -p models cache

# Create model containers (stopped by default)
echo "Creating Llama 3.1 8B container..."
docker create --name vllm-llama3-8b --gpus all -p 8001:8000 \
  -v $(pwd)/models:/models -v $(pwd)/cache:/root/.cache/hf \
  -e HF_TOKEN=${HF_TOKEN:?Set HF_TOKEN environment variable} \
  vllm/vllm-openai:v0.6.3 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --served-model-name llama3-8b \
  --download-dir /models --dtype auto \
  --max-model-len 8192 --gpu-memory-utilization 0.90

echo "Creating Qwen 2.5 14B AWQ container..."
docker create --name vllm-qwen14b-awq --gpus all -p 8002:8000 \
  -v $(pwd)/models:/models -v $(pwd)/cache:/root/.cache/hf \
  -e HF_TOKEN=${HF_TOKEN:?Set HF_TOKEN environment variable} \
  --network my-network \
  vllm/vllm-openai:v0.6.3 \
  --model Qwen/Qwen2.5-14B-Instruct-AWQ \
  --served-model-name qwen2.5-14b-awq \
  --download-dir /models --dtype auto \
  --max-model-len 6144 --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes

echo "Creating DeepSeek Coder V2 Lite container..."
docker create --name vllm-coder7b --gpus all -p 8003:8000 \
  -v $(pwd)/models:/models -v $(pwd)/cache:/root/.cache/hf \
  -e HF_TOKEN=${HF_TOKEN:?Set HF_TOKEN environment variable} \
  --network my-network \
  vllm/vllm-openai:v0.6.3 \
  --model deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct \
  --served-model-name deepseek-coder \
  --download-dir /models --dtype auto \
  --max-model-len 8192 --gpu-memory-utilization 0.90 \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser hermes

# Build and create image model container
echo "Building image inference server..."
cd "$(dirname "$0")/image-inference-server"
if [ -f "Dockerfile" ]; then
    docker build -t image-inference-server:latest . || {
        echo "Warning: Failed to build image inference server. You can build it later with:"
        echo "  cd image-inference-server && docker build -t image-inference-server:latest ."
    }
    cd ..
    
    echo "Creating Qwen Image Edit container..."
    docker create --name qwen-image-server --gpus all -p 8005:8000 \
      -v $(pwd)/models:/models -v $(pwd)/cache:/root/.cache/hf \
      -e MODEL_NAME=Qwen/Qwen-Image-Edit-2509 \
      -e HF_TOKEN=${HF_TOKEN:?Set HF_TOKEN environment variable} \
      --network my-network \
      image-inference-server:latest || {
        echo "Warning: Failed to create image model container. Make sure the image is built first."
    }
else
    echo "Warning: image-inference-server/Dockerfile not found. Skipping image model setup."
    echo "You can set it up later by running: ./build-image-server.sh"
    cd ..
fi

echo "Starting manager service..."
docker compose up -d

echo "Setup complete!"
echo "Manager is running on port 8000"
echo "Available models: llama3-8b, qwen2.5-14b-awq, deepseek-coder, qwen-image-edit"
echo ""
echo "Test with: curl http://localhost:8000/healthz"
echo "First request to any model will start the container and download the model (this may take time)"
