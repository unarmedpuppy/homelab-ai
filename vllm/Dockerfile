# Custom vLLM image with transformers v5 support.
#
# vLLM nightly pins transformers to 4.x, which doesn't support qwen3_5_text
# (Qwen3.5 architecture). By upgrading transformers after vLLM is installed,
# we enable native qwen3_5_text loading without AWQ quantization.
#
# See: https://github.com/vllm-project/vllm/pull/30566
# Once that PR merges and vLLM nightly updates, this Dockerfile can be retired
# and VLLM_IMAGE can revert to vllm/vllm-openai:nightly.
FROM vllm/vllm-openai:nightly

RUN pip install --no-cache-dir --upgrade transformers

COPY patch_vllm_config.py /app/patch_vllm_config.py

# Patch vLLM's config registry to map qwen3_5_text -> Qwen3_5TextConfig.
# vLLM nightly only maps qwen3_5 (multimodal VL) but not qwen3_5_text (text-only).
# With transformers v5, loading a qwen3_5_text model returns Qwen3_5TextConfig,
# which fails vLLM's strict isinstance check against the multimodal Qwen3_5Config.
RUN python3 /app/patch_vllm_config.py
