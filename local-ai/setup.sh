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
  vllm/vllm-openai:latest \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct \
  --served-model-name llama3-8b \
  --download-dir /models --dtype auto \
  --max-model-len 8192 --gpu-memory-utilization 0.90

echo "Creating Qwen 2.5 14B AWQ container..."
docker create --name vllm-qwen14b-awq --gpus all -p 8002:8000 \
  -v $(pwd)/models:/models -v $(pwd)/cache:/root/.cache/hf \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-14B-Instruct-AWQ \
  --served-model-name qwen2.5-14b-awq \
  --download-dir /models --dtype auto \
  --max-model-len 6144 --gpu-memory-utilization 0.90

echo "Creating DeepSeek Coder V2 Lite container..."
docker create --name vllm-coder7b --gpus all -p 8003:8000 \
  -v $(pwd)/models:/models -v $(pwd)/cache:/root/.cache/hf \
  vllm/vllm-openai:latest \
  --model deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct \
  --served-model-name deepseek-coder-7b \
  --download-dir /models --dtype auto \
  --max-model-len 8192 --gpu-memory-utilization 0.90

echo "Creating Qwen Image Edit container..."
docker create --name vllm-qwen-image --gpus all -p 8004:8000 \
  -v $(pwd)/models:/models -v $(pwd)/cache:/root/.cache/hf \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen-Image-Edit-2509 \
  --served-model-name qwen-image-edit \
  --download-dir /models --dtype auto \
  --max-model-len 4096 --gpu-memory-utilization 0.90

echo "Starting manager service..."
docker compose up -d

echo "Setup complete!"
echo "Manager is running on port 8000"
echo "Available models: llama3-8b, qwen2.5-14b-awq, deepseek-coder, qwen-image-edit"
echo ""
echo "Test with: curl http://localhost:8000/healthz"
echo "First request to any model will start the container and download the model (this may take time)"
