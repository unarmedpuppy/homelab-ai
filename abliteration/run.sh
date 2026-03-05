#!/usr/bin/env bash
# OBLITERATUS run script — Git Bash on Windows
# Usage: ./run.sh <model_id> [method] [output_subdir]
#
# Examples:
#   ./run.sh Qwen/Qwen2.5-7B-Instruct
#   ./run.sh Qwen/Qwen2.5-7B-Instruct advanced qwen2.5-7b-abliterated
#   ./run.sh meta-llama/Llama-3.1-8B-Instruct advanced llama-3.1-8b-abliterated

MODEL="${1:-Qwen/Qwen2.5-7B-Instruct}"
METHOD="${2:-advanced}"
OUTPUT_NAME="${3:-$(basename "$MODEL")-abliterated}"
HARBOR="${HARBOR_REGISTRY:-harbor.server.unarmedpuppy.com}"
OUTPUT_DIR="C:/models/abliterated/${OUTPUT_NAME}"

echo "Model:  ${MODEL}"
echo "Method: ${METHOD}"
echo "Output: ${OUTPUT_DIR}"
echo ""

mkdir -p "${OUTPUT_DIR}"

docker run --rm --gpus all \
  -v huggingface-cache:/root/.cache/huggingface \
  -v "${OUTPUT_DIR}:/output" \
  "${HARBOR}/library/obliteratus:latest" \
  obliterate "${MODEL}" \
    --method "${METHOD}" \
    --output-dir /output
