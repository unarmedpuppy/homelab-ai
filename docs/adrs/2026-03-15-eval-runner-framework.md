# ADR: Eval Runner — Homelab Model Evaluation Framework

- **Date:** 2026-03-15
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (`eval-runner/`, `docker-compose.server.yml`, `.gitea/workflows/build.yml`)
- **Tasks:** homelab-ai-029 (new)
- **Related:**
  - [2026-03-15-glm-model-garden-additions.md](2026-03-15-glm-model-garden-additions.md)
  - [2026-03-15-lightweight-model-garden-and-vllm-upgrade.md](2026-03-15-lightweight-model-garden-and-vllm-upgrade.md)

## Context

The homelab now runs 40+ models across multiple architectures (Qwen3, GLM, Gemma, Phi, LLaMA). Model selection had been based on vibes: first impressions, latency feel, and whether tool calls "seemed to work." This is not sufficient for:

- Choosing between GLM-4.7-Flash vs Qwen3-32B for agentic tasks
- Verifying that `<think>` tokens are stripped by llm-router for all reasoning models
- Confirming tool calling works correctly after vLLM upgrades
- Tracking regressions when llm-router or vLLM changes

## Decision

Build a first-class eval framework as a server-side service (port 8020) with:

1. **YAML case library** — homelab-specific eval cases, not generic benchmarks
2. **11 scorer types** — from deterministic (`tool_call`, `no_think_tags`, `word_count`) to probabilistic (`llm_judge`)
3. **LLM-as-judge** — uses the llm-router itself with qwen3-32b-awq for open-ended scoring
4. **SQLite persistence** — all runs stored for longitudinal comparison
5. **CLI** — `eval run/compare/stats` using Rich for readable output
6. **Async execution** — runs execute in background; client polls for completion

## Eval Categories

| Category | Cases | Key tests |
|---|---|---|
| `tool_use` | 6 | Tool name, arg correctness, multi-turn chains, no spurious calls |
| `instruction_following` | 8 | JSON schema, word limits, negation, numbered formats |
| `correctness` | 9 | Math, factual, code generation |
| `persona` | 5 | HAL/Avery role fidelity, out-of-scope routing |
| `thinking_tokens` | 7 | `<think>` absence across simple/complex/tool responses |
| `homelab_knowledge` | 7 | vLLM concepts, Docker GPU, CUDA, WSL2, quantization |
| `character` | 2 | Emotional nuance, honest pushback on flawed claims, genuine self-reflection on own nature — no system prompt |

## Scorer Design

All scorers are deterministic except `llm_judge`. Key design decisions:

**`no_think_tags`** — the single most important eval for this stack. Every reasoning model (Qwen3, GLM-Z1) emits `<think>` tokens. The llm-router is supposed to strip them. This scorer verifies it actually does. Tagged `smoke` — runs in every CI gate.

**`tool_call`** — checks both that the tool was called AND that required args contain expected substrings. Score 0.5 (partial) when tool name is right but args are wrong — this distinguishes "model knows to call bash" from "model knows to pass the right command."

**`llm_judge`** — rubric and response are passed as a JSON envelope, never as inline text. This prevents the eval case from injecting instructions into the judge prompt. Judge model is configurable (`JUDGE_MODEL` env var), default `qwen3-32b-awq`.

## Architecture

- Tests the **full llm-router stack**, not models in isolation. This is intentional — we care about end-to-end behavior including router sampling defaults, tool-call-parser translation, and thinking token stripping.
- Runs on the **server** (not gaming PC) — always available, no GPU needed.
- Cases are **baked into the Docker image** — image version and case library are always in sync. Hot-reload via `POST /admin/reload` for development.

## Smoke Suite (CI Gate)

The `smoke` suite (12 cases tagged `smoke`) is designed to run in under 3 minutes:
- `no_think_tags` on basic question — catches router regressions
- `tool_call` on bash — catches tool-call-parser breakage
- Math correctness (47×83=3901) — catches model degradation
- JSON schema output — catches sampling/temperature issues
- HAL persona — catches system prompt regression

Exit code 1 if pass rate < 80% — usable as a post-deploy gate.

## Usage

```bash
# Compare two models on all cases
eval run --model qwen3-32b-awq --suite full --wait
eval run --model glm-4.7-flash --suite full --wait
eval compare <run_a> <run_b>

# Smoke check after a vLLM upgrade
eval run --model qwen3-32b-awq --suite smoke --wait

# See what's performing best across all runs
eval stats
```

## Consequences

- Model choices are now data-driven, not vibe-based
- Adding a new model to the garden should be followed by `eval run --model <new-model> --suite full`
- New eval cases should be added when new failure modes are discovered (regression-driven test writing)
- The judge model consumes tokens on every `llm_judge` scorer — keep judge cases targeted, not exhaustive

## Temperature Sweep

`RunRequest` accepts `temperature_override: Optional[float]` — overrides the per-case default for a single run. The CLI `temp-sweep` command fires N runs (one per temperature), polls them all, and renders a case × temperature matrix:

```bash
eval temp-sweep -m qwen3.5-27b -s character --temps 0.0,0.5,0.7,0.9
```

Output identifies the sweet spot: the highest temperature that still clears 80% pass rate. Useful for understanding where a model opens up vs. becomes incoherent. `temperature` is stored on each `CaseResult` in the DB.

## Follow-up

- Add A2A communication eval cases (innie engine round-trip testing)
- Add latency SLA enforcement to smoke suite (P95 < 10s for simple queries)
- Wire `make eval-smoke` into post-deploy webhook on server
- Add streaming response eval (verify incremental token delivery)
