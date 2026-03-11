FROM harbor.server.unarmedpuppy.com/docker-hub/pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir nvidia-ml-py && \
    pip install --no-cache-dir \
    "git+https://github.com/vllm-project/llm-compressor.git" \
    "git+https://github.com/huggingface/transformers.git" \
    accelerate \
    sentencepiece \
    protobuf && \
    pip uninstall -y torchvision torchaudio 2>/dev/null || true

COPY quantize.py /app/quantize.py

VOLUME ["/input", "/output"]

ENTRYPOINT ["python", "/app/quantize.py"]
CMD ["--help"]
