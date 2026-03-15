# ADR: GLM Model Series — Model Garden Additions

- **Date:** 2026-03-15
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (`llm-manager/models.json`)
- **Tasks:** homelab-ai-023
- **Related:**
  - [2026-03-08-model-garden-architecture.md](2026-03-08-model-garden-architecture.md)
  - [2026-03-15-claude-code-local-routing-optimization.md](2026-03-15-claude-code-local-routing-optimization.md)

## Context

Zhipu AI (ZAI / THUDM) maintains a family of open-weight models designed for strong tool calling
and reasoning. The model garden currently contains only Qwen-series models for text inference.
GLM models offer a complementary set of capabilities:

- **GLM-4.7-Flash** is specifically recommended by Unsloth for Claude Code agentic tasks —
  fast MoE architecture with native interleaved thinking and clean tool call format.
- **GLM-Z1** series adds deep reasoning variants (9B and 32B) with thinking mode.
- **GLM-Z1-Rumination** adds an extended-thinking variant designed for long research tasks.

All four models fit on a single RTX 3090 (24GB) with appropriate quantization.

## Hardware Constraints

| Model | Params | Architecture | BF16 VRAM | Strategy | Final VRAM |
|-------|--------|--------------|-----------|----------|-----------|
| GLM-4.7-Flash | 30B total / 3B active | MoE | ~60GB | BNB 4-bit | ~16GB ✓ |
| GLM-Z1-9B | 9B | Dense | ~18GB | Native BF16 | ~18GB ✓ |
| GLM-Z1-32B | 32B | Dense | ~64GB | BNB 4-bit | ~17GB ✓ |
| GLM-Z1-Rumination-32B | 32B | Dense | ~64GB | BNB 4-bit | ~17GB ✓ |

All run on a single RTX 3090. Dual-GPU TP is not required.

## vLLM Compatibility

GLM-4.7 and GLM-Z1 models have native vLLM support as of v0.7+:

| Model | Tool-call-parser | Reasoning-parser | Notes |
|-------|-----------------|------------------|-------|
| GLM-4.7-Flash | `glm47` | `glm45` | Dedicated parser added in vLLM for 4.7 series |
| GLM-Z1-9B | `glm4` | `glm4` | Z1 uses GLM-4 base architecture |
| GLM-Z1-32B | `glm4` | `glm4` | Same as Z1-9B |
| GLM-Z1-Rumination-32B | `glm4` | `glm4` | Same as Z1-9B |

**Flags required for all GLM models in Claude Code context:**

```
--enable-auto-tool-choice
--tool-call-parser <parser>
--reasoning-parser <parser>
```

The `--enable-auto-tool-choice` flag is essential — without it, vLLM will not emit tool calls
in response to Claude Code's tool definitions even when the model would otherwise generate them.

## Quantization Decision: BNB over AWQ

Community AWQ versions of GLM-4.7-Flash exist (`cyankiwi/GLM-4.7-Flash-AWQ-4bit`,
`QuantTrio/GLM-4.7-Flash-AWQ`) but were **calibrated without tool calling data**. This causes
degraded tool call quality — the AWQ quant has not seen the tool use format during calibration,
so function call JSON generation is unreliable.

BitsAndBytes (`--load-format bitsandbytes`) quantizes the native model weights on-the-fly at
load time. This preserves the model's learned tool calling behavior at the cost of slightly
slower load times (~2-3min vs ~30s for AWQ).

GLM-Z1-9B has no AWQ available — native BF16 at 18GB fits within a single 24GB RTX 3090.

If community AWQ versions appear that were calibrated with tool calling data, they should be
preferred for GLM-4.7-Flash due to faster load times and better VRAM headroom.

## Model IDs

| Model ID (models.json) | HuggingFace | Notes |
|------------------------|-------------|-------|
| `glm-4.7-flash` | `zai-org/GLM-4.7-Flash` | Official ZAI org (newer) |
| `glm-z1-9b` | `THUDM/GLM-Z1-9B-0414` | Official THUDM org |
| `glm-z1-32b` | `THUDM/GLM-Z1-32B-0414` | Official THUDM org |
| `glm-z1-rumination-32b` | `THUDM/GLM-Z1-Rumination-32B-0414` | Official THUDM org |

## Reasoning Parser Behavior

GLM models implement **interleaved thinking** — the model can emit `<think>...</think>` tokens
before its response. The `reasoning-parser` in vLLM strips these from the final response and
surfaces them separately (or discards them depending on config).

For Claude Code sessions, thinking tokens should **not** be passed back as visible content —
Claude Code doesn't know how to handle them and would display them as raw text in the terminal.
The `reasoning-parser` flag handles this correctly: thinking is processed internally and the
response returned to Claude Code contains only the final answer or tool call.

## Consequences

- Four new models available in the model garden for on-demand loading via llm-manager
- All run single-GPU, so they don't compete with dual-GPU qwen3.5 deployments
- `glm-4.7-flash` is the recommended first model to test — fastest, best tool calling, Claude Code optimized
- BNB load times are longer than AWQ; first load will download weights (~60GB for 30B BF16)
- Parser names (`glm47`, `glm4`) need to be verified against the specific vLLM version
  deployed in vllm-custom image; if a parser is not found, vLLM will error at startup

## Testing

On first load of each model, verify tool calling works:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.7-flash",
    "messages": [{"role": "user", "content": "What files are in /tmp?"}],
    "tools": [{"type": "function", "function": {"name": "bash", "description": "Run shell command", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}],
    "tool_choice": "auto"
  }' | jq '.choices[0].message'
```

Expected: response with `tool_calls` array containing a `bash` call, not plain text.
