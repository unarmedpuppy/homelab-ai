"""AWQ quantization script using AutoAWQ (autoawq 0.2.9+, transformers 5.x).

Supports qwen3, qwen3_5, llama, mistral, and any architecture AutoAWQ can load.
Output is AWQ-compatible and loadable by vLLM with --quantization awq_marlin.
"""
import argparse
import sys
from pathlib import Path


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

    print(f"Loading model from: {model_path}")
    print(f"Output path:        {output_path}")
    print(f"Bits:               {args.bits}")
    print(f"Group size:         {args.group_size}")

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

    print(f"Saving quantized model to {output_path}...")
    model.save_quantized(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    print(f"Done. Saved to: {output_path}")


if __name__ == "__main__":
    main()
