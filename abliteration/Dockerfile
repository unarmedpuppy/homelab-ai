FROM harbor.server.unarmedpuppy.com/docker-hub/pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Pin to a specific commit for reproducibility
ARG OBLITERATUS_COMMIT=main
RUN pip install --no-cache-dir \
    git+https://github.com/elder-plinius/OBLITERATUS.git@${OBLITERATUS_COMMIT} \
    accelerate \
    sentencepiece \
    protobuf

VOLUME ["/root/.cache/huggingface", "/output"]

ENTRYPOINT ["obliteratus"]
CMD ["--help"]
