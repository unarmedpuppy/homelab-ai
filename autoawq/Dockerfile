FROM harbor.server.unarmedpuppy.com/docker-hub/pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Remove torchvision - incompatible with torch 2.5.1 when CUDA is accessible
# (causes PreTrainedModel import failure via torchvision::nms operator mismatch)
RUN pip uninstall -y torchvision torchaudio 2>/dev/null; true

# Replace deprecated pynvml to avoid CUDA init warnings
RUN pip install --no-cache-dir nvidia-ml-py

# NOTE: qwen3_5 architecture (Qwen3.5-27B) requires transformers>=5.0.0 for quantization,
# but llm-compressor 0.10.0 caps at transformers<=4.57.6, and the git version requires
# torch>=2.9.0. As of 2026-03-11, this toolchain cannot quantize qwen3_5 models.
# This Dockerfile will be updated when llm-compressor adds qwen3_5 support.
#
# For supported architectures (qwen2, qwen3, llama, etc.), this builds a working image.
RUN pip install --no-cache-dir \
    llmcompressor \
    "transformers>=4.56.1,<=4.57.6" \
    accelerate \
    sentencepiece \
    protobuf

COPY quantize.py /app/quantize.py

VOLUME ["/input", "/output"]

ENTRYPOINT ["python", "/app/quantize.py"]
CMD ["--help"]
