# Frontier Model Hardware Strategy

**Status**: Planning
**Created**: 2025-12-31
**Last Updated**: 2025-12-31
**Purpose**: Strategic hardware planning for running frontier-level open-source LLMs locally

## Executive Summary

Running true frontier models (405B+) locally is impractical for homelabs - they require 200-400GB+ VRAM. However, the **sweet spot for 2025-2026 is the 70-120B parameter range**, which delivers GPT-4 class performance and is achievable with consumer hardware.

**Recommendation**: Build a dedicated **2x RTX 3090 inference server** (48GB, ~$3,600 total build). This covers 70B INT4 and DeepSeek V3, which is GPT-4 class. The 3090 offers 90% of 4090 performance at 50% of the cost for LLM inference, and is the last consumer card with NVLink support.

### User Decisions (2025-12-31)
- **Form factor**: Full tower, separate from rack-mounted server
- **3090 in gaming PC**: Keep it there for gaming
- **Electrical**: Will need some electrical work (doable)

---

## Current State

| GPU | VRAM | Location | Role |
|-----|------|----------|------|
| RTX 3070 | 8GB | Debian Server | Always-on control plane, small models |
| RTX 3090 | 24GB | Windows Gaming PC | Burst compute, 14B-32B models |
| **Total** | **32GB** | | Covers up to ~70B INT4 with offloading |

### Current Capabilities

| Model Class | Parameters | VRAM Needed (INT4) | Current Status |
|-------------|------------|-------------------|----------------|
| Small | 7-14B | 4-8GB | ✅ Comfortable |
| Medium | 32-34B | 16-20GB | ✅ Fits 3090 |
| Large | 70-72B | 36-40GB | ⚠️ Requires offloading |
| Frontier | 120B+ | 60-80GB | ❌ Not feasible |
| True Frontier | 405B+ | 200GB+ | ❌ Datacenter only |

---

## Model VRAM Requirements (2025 Reference)

### Popular Models by Quantization

| Model | FP16 | INT8 | INT4 |
|-------|------|------|------|
| Llama 3.1 8B | 16GB | 8GB | 4GB |
| Qwen 2.5 32B | 64GB | 32GB | 16GB |
| Llama 3.1 70B | 140GB | 70GB | 35GB |
| Qwen 72B | 144GB | 72GB | 36GB |
| DeepSeek V3 (671B MoE) | 400GB+ | ~200GB | ~100GB* |
| Llama 3.1 405B | 810GB | 405GB | 203GB |

*DeepSeek V3 uses Mixture of Experts - only ~37GB active at once with smart offloading

### Key Insight: MoE Changes Everything

Mixture of Experts models like DeepSeek V3 (671B total, ~37B active) can run on surprisingly modest hardware because only a fraction of parameters are active per token. This is likely the future of "frontier" open-source models.

---

## Hardware Options Analysis

### Option 1: Consumer Multi-GPU Rack (RECOMMENDED)

**Configuration**: 4x RTX 4090 (96GB total) or 2x RTX 5090 + 2x RTX 4090 (112GB total)

| Aspect | Details |
|--------|---------|
| **Total VRAM** | 96-128GB |
| **Cost** | $7,000-12,000 (before tariff increases) |
| **Power** | 1,800-2,400W for GPUs alone |
| **Cooling** | Requires dedicated ventilation |
| **Interconnect** | PCIe only (no NVLink on consumer cards) |

**Performance Benchmarks** (from research):
- 2x RTX 5090: 80+ tokens/sec on 48GB models (beats single H100)
- 2x RTX 4090: 467 tokens/sec on same workload
- 4x RTX 4090: Can run 70B FP16 or 120B INT4

**Pros**:
- ✅ Best performance per dollar
- ✅ Can run 70B+ models at production speeds
- ✅ Consumer cards easier to source and resell
- ✅ PCIe sufficient for inference (NVLink not required)
- ✅ Upgradeable incrementally
- ✅ Huge community support (llama.cpp, vLLM, etc.)

**Cons**:
- ❌ High power consumption (need 30A circuit minimum)
- ❌ Significant cooling requirements
- ❌ Physical space (need multi-GPU chassis or external rack)
- ❌ No NVLink = some tensor parallelism overhead
- ❌ Windows gaming PC model becomes awkward at scale

**Physical Requirements**:
- Electrical: Dedicated 30A 240V circuit recommended
- Cooling: 6,000-10,000 BTU/hr exhaust capacity
- Space: Full tower or 4U+ rack chassis
- Motherboard: PCIe bifurcation support or multiple x16 slots

**Recommended Build Path**:
1. **Phase 1 (Now)**: Keep current 3070 + 3090 setup (32GB)
2. **Phase 2 (Before tariffs)**: Add 2x RTX 4090 to dedicated server (80GB total with 3090)
3. **Phase 3 (2025-2026)**: Upgrade to 5090s as prices stabilize

---

### Option 2: Mac Studio M-Series (ALTERNATIVE)

**Configuration**: Mac Studio M3 Ultra (192GB unified memory)

| Aspect | Details |
|--------|---------|
| **Total Memory** | 192GB unified |
| **Cost** | $8,000-10,000 |
| **Power** | 300-400W total system |
| **Cooling** | Built-in, quiet |
| **Form Factor** | Compact desktop |

**Performance Benchmarks**:
- 70B INT4: ~95 tokens/sec
- DeepSeek V3 671B: 21 tokens/sec (small context) → 5.79 tokens/sec (large)
- Llama 4 Maverick: 50 tokens/sec (small) → 25 tokens/sec (10k context)

**Pros**:
- ✅ Massive unified memory (192GB) - can load models that don't fit in GPU VRAM
- ✅ Extremely power efficient (~300W vs 2000W+)
- ✅ Silent operation
- ✅ No cooling infrastructure needed
- ✅ Simple, reliable, "just works"
- ✅ Can actually run 405B (slowly) via memory bandwidth

**Cons**:
- ❌ 2-4x slower than equivalent NVIDIA setup
- ❌ Memory bandwidth limited (~800 GB/s vs 3+ TB/s for multi-4090)
- ❌ Not upgradeable
- ❌ Locked to Apple ecosystem
- ❌ No CUDA (some tools don't work)
- ❌ M4 Ultra was skipped - unclear roadmap
- ❌ Context length severely impacts performance (4x slowdown)

**Best For**:
- Users who prioritize simplicity over raw speed
- Running very large models occasionally (not production inference)
- Power-constrained environments
- Those who won't tinker with Linux/CUDA

---

### Option 3: Used Professional GPUs

**Configuration**: 2x A6000 (96GB) or 2x L40S (96GB)

| Aspect | A6000 | L40S |
|--------|-------|------|
| **VRAM** | 48GB each | 48GB each |
| **Cost (2x)** | ~$9,000-10,000 | ~$15,000 |
| **Power (2x)** | 600W | 700W |
| **NVLink** | Yes (bridge available) | No |
| **FP8 Support** | No | Yes |

**Pros**:
- ✅ NVLink support (A6000) - better tensor parallelism
- ✅ ECC memory - more reliable
- ✅ Better driver support for enterprise workloads
- ✅ Quieter than gaming cards
- ✅ 48GB per card is sweet spot

**Cons**:
- ❌ Worse price/performance than consumer cards
- ❌ A6000 lacks FP8 (newer quantization methods)
- ❌ L40S expensive and no NVLink
- ❌ Harder to resell
- ❌ Enterprise drivers can lag consumer features

**Not Recommended** unless you specifically need:
- NVLink for training workloads
- ECC memory for reliability
- Enterprise support contracts

---

### Option 4: Hybrid Cloud + Local

**Configuration**: Keep current setup + cloud bursting for frontier models

| Aspect | Details |
|--------|---------|
| **Local** | 3070 + 3090 (32GB) for daily use |
| **Cloud** | RunPod/Lambda Labs for occasional 70B+ |
| **Cost** | ~$1-3/hr for 4x A100 on demand |

**Pros**:
- ✅ No upfront hardware investment
- ✅ Access to true frontier hardware (H100, etc.)
- ✅ No power/cooling infrastructure
- ✅ Can scale to any model size

**Cons**:
- ❌ Ongoing costs add up for regular use
- ❌ Latency for cloud inference
- ❌ Data leaves your network
- ❌ Dependent on cloud availability/pricing
- ❌ Doesn't build local capability

**Best For**:
- Occasional frontier model experiments
- Users who can't commit to hardware investment
- Testing before buying local hardware

---

### Option 5: Wait for Next Generation (NOT RECOMMENDED)

**Rationale**: RTX 50-series just launched, RTX 60-series ~2 years out

**Why not to wait**:
- ❌ GPU prices expected to **double in next 2 months** (tariffs)
- ❌ Current generation is already capable of 70B+ models
- ❌ Model efficiency improving faster than hardware
- ❌ Opportunity cost of not having capability

**The tariff factor**: If GPU prices double, a 4x RTX 4090 build goes from ~$8,000 to ~$16,000. Buying now locks in current pricing.

---

## Power and Ventilation Requirements

### Power Budget by Configuration

| Config | GPU Power | System | Total | Circuit Required |
|--------|-----------|--------|-------|------------------|
| Current (3070+3090) | 220W + 350W | 200W | 770W | Standard 15A |
| 2x RTX 4090 added | 900W | 300W | 1,200W | 20A dedicated |
| 4x RTX 4090 | 1,800W | 400W | 2,200W | 30A 240V |
| Mac Studio | N/A | 400W | 400W | Standard 15A |

### Cooling Requirements

| Config | Heat Output | Cooling Solution |
|--------|-------------|------------------|
| Current | ~800W | Existing rack ventilation |
| 2x 4090 added | ~1,500W | Add 2x 120mm exhaust fans |
| 4x 4090 | ~2,500W | Dedicated AC or external exhaust |
| Mac Studio | ~400W | Built-in, no changes needed |

**Rule of thumb**: 1W of compute = ~3.4 BTU/hr of cooling needed

### Electrical Considerations

For 4x RTX 4090 build:
1. **Dedicated circuit**: 30A 240V recommended
2. **UPS sizing**: 3000VA minimum for graceful shutdown
3. **PDU**: Metered PDU to monitor power draw
4. **Electrician**: May need panel upgrade ($500-2000)

---

## Open Source Model Trajectory (2025-2026)

### Key Trends

1. **Quality plateau at 70-120B**: Larger models show diminishing returns
2. **MoE dominates**: Future frontier models will be MoE (smaller active params)
3. **Distillation wins**: Smaller models trained on larger model outputs
4. **Cost collapse**: GPT-4 equivalent cost fell 240x in 18 months
5. **China leads open-source**: DeepSeek, Qwen, GLM advancing rapidly

### What to Expect

| Timeframe | Expected Models | VRAM Needed |
|-----------|-----------------|-------------|
| Now | Qwen 72B, Llama 70B, DeepSeek V3 | 36-100GB |
| Mid 2025 | GPT-4 equivalent open models | 40-80GB |
| Late 2025 | Efficient 100-120B models | 60-80GB |
| 2026 | MoE models with 30-50B active | 30-60GB |

### Implication

**Don't overbuild for 405B models** - the trend is toward more efficient architectures, not raw scale. 96-128GB VRAM will likely remain sufficient through 2026.

---

## Recommendation Matrix

| Priority | Budget | Recommendation |
|----------|--------|----------------|
| Max performance | $10-15K | 4x RTX 4090 dedicated server |
| Balanced | $5-8K | 2x RTX 4090 + keep 3090 |
| Simplicity | $8-10K | Mac Studio M3 Ultra |
| Minimal investment | $0 | Keep current + cloud bursting |
| Future-proof | $12-15K | 2x RTX 5090 + 2x RTX 4090 |

---

## Final Recommendation

### For Your Situation

Given:
- Existing 3070 + 3090 (32GB)
- Gaming PC constraint (3090 stays for gaming)
- Impending GPU price increases
- Goal of frontier-capable local inference
- Full tower preferred (separate from rack)
- Electrical work is doable

**Recommended Path**:

#### Phase 1: When Ready to Build
**Buy 2x RTX 3090** (~$1,600-2,000 total for GPUs)

- Dedicated inference VRAM: **48GB** (tensor parallel via NVLink)
- Can run: 70B INT4 comfortably, DeepSeek V3 (671B MoE)
- Gaming PC stays untouched
- Full tower build, separate from rack

**Hardware for dedicated server (full tower)**:
| Component | Recommendation | Cost |
|-----------|----------------|------|
| 2x RTX 3090 | Used, good condition | $1,800 |
| NVLink Bridge | 3-slot spacing | $80 |
| Motherboard | ASUS WS X670E (4x PCIe x16) | $500 |
| CPU | Ryzen 9 7900X (for PCIe lanes) | $400 |
| RAM | 128GB DDR5 (for model offloading) | $300 |
| PSU | Corsair HX1200i or similar 1200W | $200 |
| Case | Fractal Define 7 XL or similar | $200 |
| NVMe | 2TB for model storage | $150 |
| **Total** | | **~$3,630** |

**Why 3090 over 4090**:
- Same 48GB VRAM (the bottleneck for model size)
- 90% of token generation speed (memory-bandwidth bound)
- NVLink support (4090 has none) - better multi-GPU efficiency
- **$2,000 cheaper** - can buy 3rd GPU later

#### Phase 2: When You Outgrow 48GB
- Add 3rd RTX 3090 (72GB total) - ~$900
- OR wait for used 5090s to become affordable
- Requires HEDT platform (Threadripper) for 3+ GPUs with full lanes

#### Phase 3: Future
- 3070 on Debian server continues as always-on router/small model host
- 3090 stays in gaming PC for gaming + occasional burst
- 3090 tower becomes primary inference workhorse

### Architecture After Build

```
┌─────────────────────────────────────────────┐
│   NEW: 2x RTX 3090 Tower (48GB + NVLink)    │
│   Primary inference - 70B INT4, DeepSeek V3 │
│   Full tower, separate location             │
└─────────────────────────────────────────────┘
                    │
                    │ (network routing)
                    │
┌─────────────────────────────────────────────┐
│      Debian Server - RTX 3070 (8GB)         │
│      Always-on router + small models        │
│      Rack-mounted                           │
└─────────────────────────────────────────────┘
                    │
                    │ (optional burst)
                    │
┌─────────────────────────────────────────────┐
│      Gaming PC - RTX 3090 (24GB)            │
│      Gaming primary, inference secondary    │
└─────────────────────────────────────────────┘
```

### What This Unlocks (48GB 3090 Tower)

| Model | Params | Quantization | VRAM Needed | Status | Speed |
|-------|--------|--------------|-------------|--------|-------|
| **Qwen 2.5 72B** | 72B | INT4 | ~36GB | ✅ Comfortable | 25-35 t/s |
| **Llama 3.1 70B** | 70B | INT4 | ~35GB | ✅ Comfortable | 25-35 t/s |
| **DeepSeek V3** | 671B MoE | Dynamic | ~37GB active | ✅ Works | 15-25 t/s |
| **Qwen 2.5 32B** | 32B | FP16 | ~64GB | ⚠️ Needs RAM offload | 15-20 t/s |
| **Qwen 2.5 32B** | 32B | INT8 | ~32GB | ✅ Easy | 30-45 t/s |
| **Mixtral 8x22B** | 176B MoE | INT4 | ~45GB | ✅ Fits | 20-30 t/s |
| **Command R+** | 104B | INT4 | ~52GB | ⚠️ Light offload | 15-25 t/s |

**Capability Comparison:**

| Capability | Before (32GB) | After (48GB dedicated) |
|------------|---------------|------------------------|
| Frontier chat | 32B max | 70B comfortably |
| Coding models | 14B or slow 32B | 70B Qwen-Coder |
| Long context | Limited | 32K-128K on 70B |
| DeepSeek V3 | Can't run | Full 671B MoE |
| Concurrent users | 1 | 2-3 simultaneous |
| Local Claude-equivalent | No | Yes (70B ≈ Claude 3 Haiku+) |

**Quality Tiers:**

| Model Class | Comparable To | Your Hardware |
|-------------|---------------|---------------|
| 7-8B | GPT-3.5 (basic) | 3070 ✅ |
| 14B | GPT-3.5 (good) | 3070/3090 ✅ |
| 32-34B | GPT-3.5-turbo | 3090 tower ✅ |
| 70-72B | Claude 3 Haiku / GPT-4-mini | 3090 tower ✅ |
| DeepSeek V3 | GPT-4 | 3090 tower ✅ |

### Alternative: Mac Path

If you value simplicity over raw performance:
- **Buy Mac Studio M3 Ultra now** ($8,000-10,000)
- Retire Linux inference setup
- Accept 2-4x slower speeds for operational simplicity
- No power/cooling infrastructure needed

**I don't recommend this** for your use case because:
1. You already have CUDA infrastructure
2. You're comfortable with Linux
3. Speed matters for interactive use
4. Gaming PC situation is already complex

---

## Cost Comparison Summary

| Option | Initial Cost | Power (Annual)* | Total 3-Year |
|--------|-------------|-----------------|--------------|
| Current (do nothing) | $0 | ~$200 | $600 |
| +2x RTX 4090 | $5,500 | ~$600 | $7,300 |
| 4x RTX 4090 server | $6,500 | ~$1,000 | $9,500 |
| Mac Studio M3 Ultra | $9,000 | ~$150 | $9,450 |
| Wait + cloud | $0 | ~$200 + $1,200 cloud | $4,200 |

*Assumes 4 hours daily inference use at $0.15/kWh

---

## Action Items

### If Buying Before Tariffs (Recommended)

- [ ] Order 2x RTX 4090 immediately
- [ ] Order motherboard with 4x PCIe x16 (ASUS WS X670E or similar)
- [ ] Order 1500W PSU (Corsair HX1500i)
- [ ] Plan electrical (verify circuit capacity)
- [ ] Plan chassis (rack mount or tower)

### Electrical Prep

- [ ] Measure current circuit load
- [ ] Identify if 20A or 30A circuit available
- [ ] Get electrician quote for dedicated circuit if needed
- [ ] Size UPS for new load

### Software Prep

- [ ] Test vLLM tensor parallelism with current setup
- [ ] Benchmark llama.cpp multi-GPU on 3070+3090
- [ ] Prepare Docker configs for multi-GPU

---

## References

- [local-ai-two-gpu-architecture.md](local-ai-two-gpu-architecture.md) - Current architecture
- [gpu-rack-mount-3070.md](gpu-rack-mount-3070.md) - Physical mounting reference
- External: llama.cpp multi-GPU documentation
- External: vLLM tensor parallelism guide

---

## Deep Dive: Multi-GPU Mechanics

### How Tensor Parallelism Actually Works

You cannot simply "combine" VRAM across separate machines. A 70GB model needs 70GB in one interconnected system. Here's how multi-GPU actually works:

**Tensor Parallelism** - The model is sliced vertically. Each GPU holds a portion of every layer's weights:

```
Single GPU (can't fit):
┌─────────────────────────────────────────┐
│            70B Model (40GB)             │
│   Layer 1 | Layer 2 | ... | Layer 80    │
└─────────────────────────────────────────┘

Two GPUs (tensor parallel):
┌───────────────────┐   ┌───────────────────┐
│   GPU 0 (24GB)    │   │   GPU 1 (24GB)    │
│   Left half of    │   │   Right half of   │
│   every layer     │   │   every layer     │
└───────────────────┘   └───────────────────┘
         │                       │
         └───────┬───────────────┘
                 │
          PCIe communication
          after each layer
```

Each token generation step:
1. GPU 0 computes its half
2. GPU 1 computes its half
3. They exchange results via PCIe
4. Repeat for next layer

### Software Commands

**vLLM:**
```bash
vllm serve meta-llama/Llama-3.1-70B --tensor-parallel-size 2
```

**llama.cpp:**
```bash
./llama-server -m llama-70b.gguf --n-gpu-layers 99 --tensor-split 0.5,0.5
```

**Ollama:**
```bash
# Automatic - detects multiple GPUs
ollama run llama3.1:70b
```

The software handles splitting automatically.

### Communication Overhead

Every layer requires GPU-to-GPU communication:

| Interconnect | Bandwidth | Overhead per Token |
|--------------|-----------|-------------------|
| NVLink (A100) | 600 GB/s | ~5% |
| NVLink (3090) | 112 GB/s | ~10-15% |
| PCIe 4.0 x16 | 32 GB/s | ~20-30% |
| PCIe 3.0 x16 | 16 GB/s | ~40-50% |

### Practical Performance Impact

| Config | Theoretical Speed | Actual Speed | Efficiency |
|--------|-------------------|--------------|------------|
| 1x 3090 (24GB model) | 40 t/s | 40 t/s | 100% |
| 2x 3090 PCIe (48GB model) | 40 t/s | 30-35 t/s | 75-85% |
| 2x 3090 NVLink (48GB model) | 40 t/s | 36-38 t/s | 90-95% |

You lose ~15-25% to communication overhead. But you can run models that wouldn't fit at all on a single GPU.

---

## Deep Dive: NVLink Limitations

### Consumer NVLink Only Connects 2 GPUs

On consumer platforms, NVLink is point-to-point between exactly 2 cards:

```
What NVLink can do (consumer):

┌─────────┐         ┌─────────┐
│  3090   │◄═══════►│  3090   │   ✅ NVLink pair
└─────────┘         └─────────┘


What NVLink CANNOT do (consumer):

┌─────────┐         ┌─────────┐         ┌─────────┐         ┌─────────┐
│  3090   │◄═══════►│  3090   │◄═══════►│  3090   │◄═══════►│  3090   │   ❌ No chain
└─────────┘         └─────────┘         └─────────┘         └─────────┘
```

Only datacenter GPUs (A100, H100) have **NVSwitch** which allows all-to-all NVLink connectivity.

### NVLink Support by GPU

| GPU | NVLink Support | Notes |
|-----|----------------|-------|
| RTX 3090 | ✅ Yes | 2-way, needs bridge (~$80) |
| RTX 3090 Ti | ❌ No | Different design |
| RTX 4090 | ❌ No | Consumer NVLink dropped |
| RTX 5090 | ❌ No | PCIe only |
| A6000 | ✅ Yes | Professional card |
| A100 | ✅ Yes | + NVSwitch for multi-GPU |

**Key insight**: RTX 3090 is the last consumer card with NVLink support.

---

## Deep Dive: 4x GPU Setups

### How 4x 3090 Actually Works

Since NVLink only connects 2 GPUs on consumer, 4x setups use PCIe:

**Option A: All PCIe (Most Common)**

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ 3090 #0 │   │ 3090 #1 │   │ 3090 #2 │   │ 3090 #3 │
└────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
     │             │             │             │
     └─────────────┴──────┬──────┴─────────────┘
                          │
                    ┌─────┴─────┐
                    │    CPU    │
                    │  PCIe 4.0 │
                    └───────────┘

All communication goes through CPU/PCIe
~32 GB/s per link (shared)
```

**Option B: Two NVLink Pairs + PCIe Bridge**

```
┌─────────┐ NVLink ┌─────────┐       ┌─────────┐ NVLink ┌─────────┐
│ 3090 #0 │◄══════►│ 3090 #1 │       │ 3090 #2 │◄══════►│ 3090 #3 │
└────┬────┘        └────┬────┘       └────┬────┘        └────┬────┘
     │                  │                 │                  │
     └────────┬─────────┘                 └────────┬─────────┘
              │                                    │
              │◄──────────── PCIe ────────────────►│
              │         (~32 GB/s)                 │

Within pairs: 112 GB/s (fast)
Between pairs: 32 GB/s (slow)
```

### Scaling Overhead

| GPUs | Total VRAM | Communication Pattern | Overhead |
|------|------------|----------------------|----------|
| 1 | 24GB | None | 0% |
| 2 | 48GB | 1 link | 15-25% |
| 4 | 96GB | 6 links (all-pairs) | 30-50% |
| 8 | 192GB | 28 links | 50-70% |

**Why overhead grows**: Tensor parallelism requires all GPUs to sync after each layer. More GPUs = more waiting.

### 4x 3090 Physical Requirements

| Challenge | Details |
|-----------|---------|
| **Motherboard** | Need 4x PCIe x16 physical slots (HEDT/server board) |
| **PCIe lanes** | Threadripper (64 lanes) or EPYC - consumer CPUs don't have enough |
| **Power** | 4x 350W = 1,400W just for GPUs. Need 1600W+ PSU |
| **Cooling** | 1,400W of heat in one case. Serious airflow required |
| **Physical space** | 4x triple-slot cards = 12 slots worth of GPU |
| **Cost** | 4x $900 = $3,600 in GPUs + $800 HEDT motherboard + $600 Threadripper |

### When to Use 4x GPUs

| Config | Sweet Spot For | Worth It? |
|--------|----------------|-----------|
| 2x 3090 (48GB) | 70B INT4, DeepSeek V3 | ✅ Yes - best value |
| 4x 3090 (96GB) | 70B FP16, 120B INT4 | ⚠️ Maybe - diminishing returns |
| 8x 3090 (192GB) | 70B+ FP16 with headroom | ❌ Buy datacenter GPUs instead |

---

## Deep Dive: RTX 3090 vs 4090 for LLM Inference

### Head-to-Head Comparison

| Spec | 2x RTX 3090 | 2x RTX 4090 |
|------|-------------|-------------|
| **Total VRAM** | 48GB | 48GB |
| **Memory Bandwidth** | 1,872 GB/s | 2,016 GB/s |
| **FP16 Compute** | 71 TFLOPS | 165 TFLOPS |
| **TDP** | 700W | 900W |
| **Street Price** | ~$1,600-2,000 | ~$3,600-4,000 |
| **NVLink** | ✅ Yes | ❌ No |
| **Price Difference** | — | **+$2,000** |

### Why This Matters for LLMs

LLM inference has two phases:

1. **Prompt processing** (compute-bound) → 4090 wins by ~2x
2. **Token generation** (memory-bandwidth-bound) → Nearly identical

For interactive chat, you spend most time in token generation. The bottleneck is moving weights from VRAM to compute units, limited by memory bandwidth.

**Memory bandwidth difference: only 8%** (936 GB/s vs 1008 GB/s per card)

### Real-World Speed Comparison

| Task | 2x 3090 | 2x 4090 | Difference |
|------|---------|---------|------------|
| Load 70B model | ~30 sec | ~25 sec | 4090 slightly faster |
| Process 2K prompt | ~3 sec | ~1.5 sec | **4090 2x faster** |
| Generate tokens | ~30 t/s | ~35 t/s | 4090 ~15% faster |
| **Typical chat feel** | Fast | Slightly faster | Barely noticeable |

### When 4090 Actually Matters

| Use Case | 3090 | 4090 | Winner |
|----------|------|------|--------|
| Single-user chat | Good | Slightly better | **3090** (value) |
| Long prompts (10K+) | Slower | Faster | 4090 |
| Batched inference (multi-user) | Limited | Better | 4090 |
| Fine-tuning | Slow | 2x faster | 4090 |
| Image generation | Slower | 2x faster | 4090 |

### Value Analysis

**For single-user LLM inference:**

| Option | Cost | Speed | Value Rating |
|--------|------|-------|--------------|
| 2x 3090 | ~$1,800 | 85-90% of 4090 | ⭐⭐⭐⭐⭐ |
| 2x 4090 | ~$3,800 | 100% | ⭐⭐⭐ |

**2x 3090s at $1,800 gets you 90% of the performance for 50% of the cost.**

### 3090 Advantages

1. **Same VRAM** (48GB) - the actual bottleneck for model size
2. **Similar memory bandwidth** - the bottleneck for token generation
3. **NVLink support** - slightly better multi-GPU efficiency
4. **$2,000 savings** - can buy a 3rd GPU later

### When to Buy 4090 Instead

- You plan to serve multiple concurrent users
- You'll do fine-tuning/training
- You want FP8 quantization support
- Long prompt processing speed matters
- Money isn't the constraint

---

## Revised Recommendation: 2x RTX 3090

### Updated Build (Best Value)

Given the analysis above, **2x RTX 3090 is the better value** for single-user LLM inference:

| Component | Recommendation | Cost |
|-----------|----------------|------|
| 2x RTX 3090 | Used, good condition | $1,800 |
| NVLink Bridge | 3-slot spacing | $80 |
| Motherboard | ASUS WS X670E or similar | $500 |
| CPU | Ryzen 9 7900X | $400 |
| RAM | 128GB DDR5 | $300 |
| PSU | 1200W (lower than 4090 build) | $200 |
| Case | Full tower | $200 |
| NVMe | 2TB | $150 |
| **Total** | | **~$3,630** |

**Savings vs 4090 build: ~$2,000**

### What to Do with Savings

- 3rd RTX 3090 later (72GB total)
- Electrical work for dedicated circuit
- Better UPS
- Future 5090 upgrade fund

---

## Appendix: GPU Comparison Table

| GPU | VRAM | FP16 TFLOPS | TDP | MSRP | Street Price (Dec 2024) |
|-----|------|-------------|-----|------|------------------------|
| RTX 3070 | 8GB | 20.3 | 220W | $499 | $350-400 |
| RTX 3090 | 24GB | 35.6 | 350W | $1,499 | $800-1,000 |
| RTX 4090 | 24GB | 82.6 | 450W | $1,599 | $1,800-2,000 |
| RTX 5090 | 32GB | ~100+ | 575W | $1,999 | $2,500+ (scarce) |
| A6000 | 48GB | 38.7 | 300W | $4,650 | $4,400-4,800 |
| L40S | 48GB | 91.6 | 350W | $8,000 | $7,500+ |
| A100 80GB | 80GB | 77.9 | 400W | $15,000 | $10,000-14,000 |

