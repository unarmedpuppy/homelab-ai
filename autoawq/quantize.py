"""AutoAWQ quantization script for local models."""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Quantize a model with AutoAWQ")
    parser.add_argument("--model-path", required=True, help="Path to input model (BF16)")
    parser.add_argument("--output-path", required=True, help="Path to save quantized model")
    parser.add_argument("--group-size", type=int, default=128, help="AWQ group size (default: 128)")
    args = parser.parse_args()

    model_path = Path(args.model_path)
    output_path = Path(args.output_path)

    if not model_path.exists():
        print(f"Error: model path does not exist: {model_path}", file=sys.stderr)
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading model from: {model_path}")
    print(f"Output path: {output_path}")
    print(f"Group size: {args.group_size}")

    from awq import AutoAWQForCausalLM
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
    model = AutoAWQForCausalLM.from_pretrained(
        str(model_path),
        low_cpu_mem_usage=True,
        use_cache=False,
    )

    quant_config = {
        "zero_point": True,
        "q_group_size": args.group_size,
        "w_bit": 4,
        "version": "gemm",
    }
    print(f"Quantizing with config: {quant_config}")
    model.quantize(tokenizer, quant_config=quant_config)

    print(f"Saving quantized model to: {output_path}")
    model.save_quantized(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    print("Done.")


if __name__ == "__main__":
    main()
