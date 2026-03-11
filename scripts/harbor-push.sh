#!/usr/bin/env bash
# Push a quantized model directory to Harbor using ORAS.
# Usage: ./harbor-push.sh <model_dir> <tag>
# Example: ./harbor-push.sh C:/models/quantized/qwopus-27b-awq qwopus-27b-awq
set -euo pipefail

MODEL_DIR="${1:?Usage: harbor-push.sh <model_dir> <tag>}"
TAG="${2:?Usage: harbor-push.sh <model_dir> <tag>}"
HARBOR="${HARBOR_REGISTRY:-harbor.server.unarmedpuppy.com}"

echo "Pushing ${MODEL_DIR} -> ${HARBOR}/models/${TAG}:latest"
oras push "${HARBOR}/models/${TAG}:latest" "${MODEL_DIR}/."
echo "Done."
