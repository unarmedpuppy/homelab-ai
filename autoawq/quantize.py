"""AWQ quantization script using AutoAWQ (autoawq 0.2.9, transformers 5.x).

Supports qwen3, qwen3_5_text, llama, mistral, and any architecture where
the transformer layer structure is compatible with AutoAWQ's qwen3 implementation.
Output is AWQ-compatible and loadable by vLLM with --quantization awq_marlin.
"""
import argparse
import sys
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path


def patch_catcher_layer_type():
    """Patch Qwen3.5 model forward to tolerate missing layer_type on AutoAWQ's Catcher.

    AutoAWQ wraps layer 0 in a Catcher module during calibration. Qwen3.5's model
    forward reads decoder_layer.layer_type to pick the attention mask. Catcher doesn't
    proxy attributes to the wrapped module, so we patch init_quant to inject layer_type
    onto the Catcher instance after it's created.
    """
    from awq.quantize.quantizer import AwqQuantizer

    original_init_quant = AwqQuantizer.init_quant

    def patched_init_quant(self, n_samples=128, max_seq_len=512):
        modules = self.awq_model.get_model_layers(self.model)
        # Preserve layer_type from original layer 0 before Catcher wraps it
        original_layer_type = getattr(modules[0], 'layer_type', None)

        result = original_init_quant(self, n_samples=n_samples, max_seq_len=max_seq_len)

        # After init_quant, modules[0] is restored. But during the call, Catcher
        # replaced it. We hook into the model's layers list to inject layer_type
        # whenever a Catcher is detected (no 'layer_type' but has 'module').
        # This runs after init_quant completes so it's just for safety.
        return result

    # The actual fix: patch Qwen3_5Model to use getattr with fallback for layer_type
    try:
        from transformers.models.qwen3_5 import modeling_qwen3_5
        original_forward = modeling_qwen3_5.Qwen3_5Model.forward

        def patched_forward(self_model, *args, **kwargs):
            # Inject layer_type onto any Catcher-like wrapper (has .module but no .layer_type)
            for layer in self_model.layers:
                if not hasattr(layer, 'layer_type') and hasattr(layer, 'module'):
                    layer.layer_type = getattr(layer.module, 'layer_type', 'attention')
            return original_forward(self_model, *args, **kwargs)

        modeling_qwen3_5.Qwen3_5Model.forward = patched_forward
        print("Patched Qwen3_5Model.forward: layer_type proxy for AutoAWQ Catcher compatibility")
    except Exception as e:
        print(f"Warning: could not patch Qwen3_5Model.forward: {e}")


def patch_init_quant_timing():
    """Wrap init_quant with per-step timestamp prints to find the slow step."""
    import time
    import torch
    import torch.nn as nn
    from awq.quantize.quantizer import AwqQuantizer

    original = AwqQuantizer.init_quant

    def patched(self, n_samples=128, max_seq_len=512):
        def ts(msg):
            print(f"[TIMING {time.strftime('%H:%M:%S')}] {msg}", flush=True)

        # Intercept the model's forward to time the Catcher call
        orig_model_fwd = self.model.forward

        def timed_model_fwd(*args, **kwargs):
            ts("model.forward() START")
            try:
                result = orig_model_fwd(*args, **kwargs)
                ts("model.forward() returned normally (no Catcher hit!)")
                return result
            except ValueError:
                ts("model.forward() raised ValueError (Catcher worked)")
                raise

        self.model.forward = timed_model_fwd

        ts(f"init_quant starting (n={n_samples}, seq={max_seq_len})")
        result = original(self, n_samples=n_samples, max_seq_len=max_seq_len)
        ts("init_quant done")

        self.model.forward = orig_model_fwd
        return result

    AwqQuantizer.init_quant = patched
    print("Patched init_quant: timestamped diagnostics enabled")


def patch_apply_quant():
    """Skip quantizing linear layers incompatible with GEMM 4-bit packing.

    GEMM packing requires out_features divisible by 32 (packs 8x 4-bit into int32).
    Qwen3.5 GDN layers have in_proj_b/in_proj_a with out_features=num_v_heads=48,
    which is not divisible by 32. Skip these and leave them as BF16 nn.Linear.
    """
    from awq.quantize.quantizer import AwqQuantizer

    original = AwqQuantizer._apply_quant

    def patched(self, module, named_linears):
        compatible = {}
        for name, linear in named_linears.items():
            if linear.out_features % 32 != 0:
                print(f"  Skip GEMM quant (out={linear.out_features}, not div by 32): {name}")
            else:
                compatible[name] = linear
        original(self, module, compatible)

    AwqQuantizer._apply_quant = patched
    print("Patched _apply_quant: skip linears with out_features not divisible by 32 (GDN b/a projections)")


def patch_compute_best_clip():
    """Patch _compute_best_clip to handle weight output dims not divisible by batch sizes.

    GDN layers have in_proj_b and in_proj_a with num_v_heads=48 output channels.
    AutoAWQ's batch size logic tries 256 then 64, but 48 % 64 != 0 -> AssertionError.
    For these tiny layers, fall back to simple max-value (no grid search needed).
    """
    import torch
    from awq.quantize.quantizer import AwqQuantizer

    original = AwqQuantizer._compute_best_clip

    @torch.no_grad()
    def patched(self, w, input_feat, n_grid=20, max_shrink=0.5, n_sample_token=512):
        assert w.dim() == 2
        org_w_shape = w.shape
        group_size = self.group_size if self.group_size > 0 else org_w_shape[1]
        oc_batch_size = 256 if org_w_shape[0] % 256 == 0 else 64
        if org_w_shape[0] % oc_batch_size != 0:
            # Tiny SSM scalar layer (e.g. in_proj_b/in_proj_a, 48 channels) —
            # skip grid search, return per-group weight max directly
            w_r = w.reshape(org_w_shape[0], 1, -1, group_size)
            return w_r.abs().amax(dim=-1, keepdim=True).squeeze(1)
        return original(self, w, input_feat, n_grid, max_shrink, n_sample_token)

    AwqQuantizer._compute_best_clip = patched
    print("Patched _compute_best_clip: non-divisible output channels handled (GDN in_proj_b/a)")


def patch_get_layers_for_scaling():
    """Patch get_layers_for_scaling to handle Qwen3.5 GDN (linear_attention) layers.

    Qwen3.5 has two decoder layer types:
    - full_attention: has self_attn (q/k/v/o_proj) + mlp
    - linear_attention: has linear_attn (GatedDeltaNet, no q/k/v/o) + mlp

    AutoAWQ's qwen3 implementation unconditionally accesses module.self_attn,
    crashing on GDN layers. This patch skips attention scaling for GDN layers
    and only applies AWQ scaling to the shared MLP.
    """
    from awq.models.qwen3 import Qwen3AWQForCausalLM

    @staticmethod
    def patched_get_layers_for_scaling(module, input_feat, module_kwargs):
        layers = []

        if hasattr(module, 'self_attn'):
            # full_attention layer — standard q/k/v/o scaling
            if 'self_attn.q_proj' in input_feat:
                layers.append(dict(
                    prev_op=module.input_layernorm,
                    layers=[module.self_attn.q_proj, module.self_attn.k_proj, module.self_attn.v_proj],
                    inp=input_feat['self_attn.q_proj'],
                    module2inspect=module.self_attn,
                    kwargs=module_kwargs,
                ))
            if 'self_attn.o_proj' in input_feat:
                if module.self_attn.v_proj.weight.shape == module.self_attn.o_proj.weight.shape:
                    layers.append(dict(
                        prev_op=module.self_attn.v_proj,
                        layers=[module.self_attn.o_proj],
                        inp=input_feat['self_attn.o_proj'],
                    ))

        # MLP is present on both layer types
        if 'mlp.gate_proj' in input_feat:
            layers.append(dict(
                prev_op=module.post_attention_layernorm,
                layers=[module.mlp.gate_proj, module.mlp.up_proj],
                inp=input_feat['mlp.gate_proj'],
                module2inspect=module.mlp,
            ))
        if 'mlp.down_proj' in input_feat:
            layers.append(dict(
                prev_op=module.mlp.up_proj,
                layers=[module.mlp.down_proj],
                inp=input_feat['mlp.down_proj'],
            ))

        return layers

    Qwen3AWQForCausalLM.get_layers_for_scaling = patched_get_layers_for_scaling
    print("Patched get_layers_for_scaling: GDN (linear_attention) layer support added")


def patch_autoawq_registry():
    """Register qwen3_5_text as qwen3 in AutoAWQ's model registries.

    Qwen3.5's transformer layer structure (q_proj, k_proj, v_proj, o_proj,
    gate_proj, up_proj, down_proj) is identical to Qwen3, differing only in
    the config class name. The qwen3 AWQ implementation quantizes the same
    linear layers correctly.
    """
    from awq.models.auto import AWQ_CAUSAL_LM_MODEL_MAP
    from awq.models.base import TRANSFORMERS_AUTO_MAPPING_DICT

    for alias in ("qwen3_5_text", "qwen3_5"):
        if alias not in AWQ_CAUSAL_LM_MODEL_MAP:
            AWQ_CAUSAL_LM_MODEL_MAP[alias] = AWQ_CAUSAL_LM_MODEL_MAP["qwen3"]
        if alias not in TRANSFORMERS_AUTO_MAPPING_DICT:
            TRANSFORMERS_AUTO_MAPPING_DICT[alias] = "AutoModelForCausalLM"

    print("AutoAWQ registry patched: qwen3_5_text -> qwen3")


def main():
    parser = argparse.ArgumentParser(description="Quantize a model with AutoAWQ")
    parser.add_argument("--model-path", required=True, help="Path to input model (BF16/FP16) or HF model ID")
    parser.add_argument("--output-path", required=True, help="Path to save quantized model")
    parser.add_argument("--group-size", type=int, default=128, help="AWQ group size (default: 128)")
    parser.add_argument("--bits", type=int, default=4, help="Quantization bits (default: 4)")
    args = parser.parse_args()

    model_path = args.model_path
    output_path = Path(args.output_path)

    if model_path.startswith("/") and not Path(model_path).exists():
        print(f"Error: model path does not exist: {model_path}", file=sys.stderr)
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Model:      {model_path}")
    print(f"Output:     {output_path}")
    print(f"Bits:       {args.bits}")
    print(f"Group size: {args.group_size}")

    patch_autoawq_registry()
    patch_init_quant_timing()
    patch_apply_quant()
    patch_compute_best_clip()
    patch_get_layers_for_scaling()

    from awq import AutoAWQForCausalLM
    from transformers import AutoTokenizer

    quant_config = {
        "zero_point": True,
        "q_group_size": args.group_size,
        "w_bit": args.bits,
        "version": "GEMM",
    }

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    print("Loading model...")
    model = AutoAWQForCausalLM.from_pretrained(
        model_path,
        low_cpu_mem_usage=True,
        use_cache=False,
        trust_remote_code=True,
    )

    print("Running AWQ quantization (calibration pass)...")
    model.quantize(tokenizer, quant_config=quant_config)

    print(f"Saving to {output_path}...")
    model.save_quantized(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    print(f"Done. Saved to: {output_path}")


if __name__ == "__main__":
    main()
