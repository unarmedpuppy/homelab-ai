"""AWQ quantization script using llm-compressor (vLLM's AutoAWQ successor).

Supports any model architecture that transformers can load, including qwen3_5.
Output is AWQ-compatible and loadable by vLLM with quantization=awq_marlin.
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Quantize a model with llm-compressor AWQ")
    parser.add_argument("--model-path", required=True, help="Path to input model (BF16) or HF model ID")
    parser.add_argument("--output-path", required=True, help="Path to save quantized model")
    parser.add_argument("--group-size", type=int, default=128, help="AWQ group size (default: 128)")
    args = parser.parse_args()

    model_path = args.model_path
    output_path = Path(args.output_path)

    # Only validate local paths; HF model IDs don't need to exist on disk
    if not model_path.startswith("/") or Path(model_path).exists():
        pass
    else:
        print(f"Error: model path does not exist: {model_path}", file=sys.stderr)
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading model from: {model_path}")
    print(f"Output path: {output_path}")
    print(f"Group size: {args.group_size}")

    from llmcompressor import oneshot
    from llmcompressor.modifiers.quantization import QuantizationModifier

    recipe = QuantizationModifier(
        targets="Linear",
        scheme="W4A16",
        ignore=["lm_head"],
    )

    print("Running oneshot AWQ quantization...")
    oneshot(
        model=model_path,
        recipe=recipe,
        output_dir=str(output_path),
    )

    print(f"Done. Saved to: {output_path}")


if __name__ == "__main__":
    main()
