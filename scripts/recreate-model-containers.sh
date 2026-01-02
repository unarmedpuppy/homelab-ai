#!/bin/bash

# Recreate model containers with tool calling support
# Run this on the gaming PC to enable function calling

set -e

echo "This script will recreate model containers with tool calling enabled."
echo "The manager will remain running - it will just use the new containers."
echo ""

# Stop and remove old containers
echo "Stopping and removing old containers..."
docker stop vllm-qwen14b-awq vllm-coder7b 2>/dev/null || true
docker rm vllm-qwen14b-awq vllm-coder7b 2>/dev/null || true

cd "$(dirname "$0")"

echo ""
echo "Creating Qwen 2.5 14B AWQ container (with tool calling)..."
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

echo ""
echo "Creating DeepSeek Coder V2 Lite container (with tool calling)..."
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

echo ""
echo "Done! Containers recreated with tool calling support."
echo ""
echo "Test with:"
echo '  curl -X POST http://localhost:8000/v1/chat/completions \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '\''{"model": "qwen2.5-14b-awq", "messages": [{"role": "user", "content": "What is the weather?"}], "tools": [{"type": "function", "function": {"name": "get_weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}}}]}'\'''
