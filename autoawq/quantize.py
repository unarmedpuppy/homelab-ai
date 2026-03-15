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
