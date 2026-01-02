#!/bin/bash

# Build script for image inference server
# This builds the Docker image for the image model inference server

echo "Building image inference server..."

cd "$(dirname "$0")/image-inference-server"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "Error: Dockerfile not found in image-inference-server/"
    exit 1
fi

# Build the image
echo "Building Docker image: image-inference-server:latest"
docker build -t image-inference-server:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Image built successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Run setup.sh to create the container"
    echo "2. Or manually create container:"
    echo "   docker create --name qwen-image-server --gpus all -p 8005:8000 \\"
    echo "     -v \$(pwd)/models:/models -v \$(pwd)/cache:/root/.cache/hf \\"
    echo "     -e MODEL_NAME=Qwen/Qwen-Image-Edit-2509 \\"
    echo "     -e HF_TOKEN=your_token_here \\"
    echo "     --network my-network \\"
    echo "     image-inference-server:latest"
else
    echo "Error: Build failed"
    exit 1
fi

