# Frontier Model Hardware Strategy

**Status**: Planning
**Created**: 2025-12-31
**Last Updated**: 2025-12-31
**Purpose**: Strategic hardware planning for running frontier-level open-source LLMs locally

## Executive Summary

Running true frontier models (405B+) locally is impractical for homelabs - they require 200-400GB+ VRAM. However, the **sweet spot for 2025-2026 is the 70-120B parameter range**, which delivers GPT-4 class performance and is achievable with consumer hardware.

**Recommendation**: Build toward **96-128GB total VRAM** using consumer GPUs (4x RTX 4090 or 2x RTX 5090 + existing cards). This covers 70B models at full precision and 120B+ at INT4/INT8, which is where open-source development is heading.

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
- Gaming PC constraint (3090 shared with gaming)
- Impending GPU price increases
- Goal of frontier-capable local inference

**Recommended Path**:

#### Phase 1: Immediate (Before Tariffs - January 2025)
**Buy 2x RTX 4090** (~$3,600-4,000 total)

- Total VRAM: 32GB (existing) + 48GB (new) = **80GB**
- Can run: 70B INT4 comfortably, 70B INT8 with some offload
- Keeps gaming PC separate
- Build dedicated inference server (new chassis, PSU, motherboard)

**Hardware for dedicated server**:
| Component | Recommendation | Cost |
|-----------|----------------|------|
| 2x RTX 4090 | ASUS TUF or similar | $3,600 |
| Motherboard | ASUS WS X670E (4x PCIe x16) | $500 |
| CPU | Ryzen 9 7900X (for PCIe lanes) | $400 |
| RAM | 128GB DDR5 (for model offloading) | $300 |
| PSU | Corsair HX1500i or be quiet! 1500W | $300 |
| Chassis | Define 7 XL or 4U rack | $200-400 |
| NVMe | 2TB for model storage | $150 |
| **Total** | | **~$5,500-6,000** |

#### Phase 2: Mid 2025
- Evaluate RTX 5090 pricing post-tariff adjustment
- Consider adding 2 more 4090s OR upgrading to 5090s
- Target: 128GB+ total VRAM

#### Phase 3: When Needed
- Retire 3070 from inference (keep for dev/testing)
- Consolidate to dedicated multi-GPU server
- 3090 returns to pure gaming duty

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

