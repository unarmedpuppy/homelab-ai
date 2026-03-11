#!/usr/bin/env bash
# Usage: ./run.sh <input_path> <output_name>
# Example: ./run.sh C:/models/abliterated/qwopus-27b-abliterated qwopus-27b-awq
set -euo pipefail

INPUT_PATH="${1:?Usage: run.sh <input_path> <output_name>}"
OUTPUT_NAME="${2:?Usage: run.sh <input_path> <output_name>}"
OUTPUT_DIR="C:/models/quantized/${OUTPUT_NAME}"
GROUP_SIZE="${AWQ_GROUP_SIZE:-128}"

echo "Input:      ${INPUT_PATH}"
echo "Output:     ${OUTPUT_DIR}"
echo "Group size: ${GROUP_SIZE}"

docker run --rm --gpus all \
  -v "${INPUT_PATH}:/input:ro" \
  -v "${OUTPUT_DIR}:/output" \
  autoawq:latest \
  --model-path /input --output-path /output --group-size "${GROUP_SIZE}"
