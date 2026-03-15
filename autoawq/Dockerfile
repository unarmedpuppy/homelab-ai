FROM harbor.server.unarmedpuppy.com/docker-hub/pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Remove torchvision - incompatible with torch 2.5.1 when CUDA is accessible
# (causes PreTrainedModel import failure via torchvision::nms operator mismatch)
RUN pip uninstall -y torchvision torchaudio 2>/dev/null; true

# Replace deprecated pynvml to avoid CUDA init warnings
RUN pip install --no-cache-dir nvidia-ml-py

# autoawq 0.2.9+ supports qwen3, qwen3_5, llama, mistral, etc.
# transformers 5.x required for qwen3_5_text architecture (Qwen3.5 models)
RUN pip install --no-cache-dir \
    autoawq \
    transformers \
    accelerate \
    sentencepiece \
    protobuf

COPY quantize.py /app/quantize.py
COPY patch_catcher.py /app/patch_catcher.py

# Patch AutoAWQ's Catcher class to proxy attribute lookups to the wrapped module.
# Qwen3.5 has a hybrid attention architecture that reads decoder_layer.layer_type
# during forward. AutoAWQ's Catcher hook doesn't forward unknown attributes, causing
# AttributeError during calibration. This sed adds __getattr__ to the Catcher class.
RUN python /app/patch_catcher.py

VOLUME ["/input", "/output"]

ENTRYPOINT ["python", "/app/quantize.py"]
CMD ["--help"]
