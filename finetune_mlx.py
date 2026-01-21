#!/usr/bin/env python3
"""
Fine-tune Phi-3.5-mini on your Medium articles using MLX.

=============================================================================
WHAT DOES THIS SCRIPT DO?
=============================================================================
This script teaches an AI model to write like YOU. It takes a pre-trained
language model (Phi-3.5-mini) and trains it on your Medium articles so it
learns your writing style, vocabulary, and perspectives.

WHAT IS FINE-TUNING?
Pre-trained models like Phi-3.5 already know how to write English, but they
don't know YOUR voice. Fine-tuning is like having a ghostwriter study all
your work until they can mimic your style perfectly.

WHAT IS MLX?
MLX is Apple's machine learning framework, optimized for Apple Silicon (M1/M2/M3/M4).
It makes training AI models on a Mac surprisingly fast and memory-efficient.
Without MLX, fine-tuning would require expensive cloud GPUs.

WHAT IS LoRA?
LoRA (Low-Rank Adaptation) is a clever technique that lets us fine-tune
a model by only training a small "adapter" layer instead of the whole model.
Benefits:
- Uses ~10x less memory
- Trains ~10x faster
- Keeps the original model intact
- Produces small adapter files (a few MB vs gigabytes)

HOW IT WORKS:
1. Download the base model (Phi-3.5-mini-instruct)
2. Add tiny LoRA adapter layers to the model
3. Train ONLY those adapters on your article data
4. Save the adapter weights (can be loaded later)

=============================================================================

Usage:
    python finetune_mlx.py                           # Train with defaults
    python finetune_mlx.py --steps 500 --lr 5e-5    # Custom settings
    python finetune_mlx.py --resume                  # Resume from checkpoint

Prerequisites:
    pip install mlx mlx-lm
    python prepare_medium_data.py --all  # Generate training data first

Hardware:
    - Apple M1/M2/M3/M4 with 16GB+ RAM recommended
    - M4 with 24GB RAM is ideal for this model
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import shutil

import rag_config as cfg

# =============================================================================
# CHECK FOR MLX
# =============================================================================
# MLX is required for Apple Silicon training. If not installed, we exit early
# with helpful installation instructions.

try:
    import mlx.core as mx
    from mlx_lm import load, generate
except ImportError:
    print("MLX not installed. Install with: pip install mlx mlx-lm")
    sys.exit(1)


# =============================================================================
# TRAINING DATA VERIFICATION
# =============================================================================

def check_training_data(data_dir: Path) -> bool:
    """
    Verify training data exists.

    MLX-LM expects two files:
    - train.jsonl: Training examples (90% of your data)
    - valid.jsonl: Validation examples (10% for checking overfitting)

    These are created by running: python prepare_medium_data.py --all
    """
    train_file = data_dir / "train.jsonl"
    valid_file = data_dir / "valid.jsonl"

    if not train_file.exists() or not valid_file.exists():
        return False

    # Count how many examples we have
    with open(train_file) as f:
        train_count = sum(1 for _ in f)
    with open(valid_file) as f:
        valid_count = sum(1 for _ in f)

    print(f"Training data: {train_count} train, {valid_count} valid examples")
    return train_count > 0 and valid_count > 0


# =============================================================================
# MAIN TRAINING FUNCTION
# =============================================================================

def run_mlx_lm_lora(
    model: str,
    data_dir: Path,
    output_dir: Path,
    train_steps: int = 1000,
    batch_size: int = 1,
    learning_rate: float = 1e-4,
    lora_rank: int = 16,
    lora_layers: int = 16,
    grad_accumulate: int = 4,
    warmup_steps: int = 50,
    eval_steps: int = 100,
    save_steps: int = 200,
    use_weights: bool = True,
    resume: bool = False,
):
    """
    Run MLX-LM LoRA fine-tuning.

    WHAT HAPPENS DURING TRAINING:
    1. The base model is loaded into memory
    2. Small LoRA adapter matrices are added to key layers
    3. Only these adapters are trained (the rest of the model is frozen)
    4. Every `save_steps`, a checkpoint is saved so you can resume later
    5. Every `eval_steps`, we check performance on validation data

    HYPERPARAMETERS EXPLAINED:
    - train_steps: Total training iterations. More = potentially better, but
      diminishing returns after ~500-1000 for personal writing style.

    - batch_size: How many examples per step. 1 is safest for limited RAM.

    - learning_rate: How fast the model learns. Too high = unstable training,
      too low = very slow progress. 1e-4 is a good default.

    - lora_rank: Size of the adapter matrices. Higher = more capacity to learn,
      but also more memory. 16 is a good balance.

    - lora_layers: How many layers get LoRA adapters. More layers = learns more
      nuanced patterns, but uses more memory.

    - grad_accumulate: Simulates larger batches by accumulating gradients over
      multiple steps before updating. Helps with small batch sizes.

    - warmup_steps: Gradually increases learning rate at the start. Prevents
      the model from making wild changes early in training.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build the MLX-LM command
    # We use subprocess to call the mlx_lm.lora module as a command-line tool
    cmd = [
        sys.executable, "-m", "mlx_lm.lora",
        "--model", model,                       # Base model to fine-tune
        "--train",                              # Training mode
        "--data", str(data_dir),                # Where to find train.jsonl/valid.jsonl
        "--adapter-path", str(output_dir / "adapters"),  # Where to save adapters
        "--iters", str(train_steps),            # Number of training steps
        "--batch-size", str(batch_size),        # Examples per step
        "--learning-rate", str(learning_rate),  # How fast to learn
        "--lora-rank", str(lora_rank),          # LoRA adapter size
        "--lora-layers", str(lora_layers),      # Number of layers with adapters
        "--grad-checkpoint",                    # Memory optimization
        "--steps-per-eval", str(eval_steps),    # How often to validate
        "--save-every", str(save_steps),        # How often to save checkpoints
    ]

    # If resuming from a previous run, specify the adapter checkpoint
    if resume and (output_dir / "adapters").exists():
        cmd.extend(["--resume-adapter-file", str(output_dir / "adapters" / "adapters.safetensors")])
        print("Resuming from checkpoint...")

    # Print training configuration
    print(f"\nStarting MLX-LM LoRA training...")
    print(f"Model: {model}")
    print(f"Output: {output_dir}")
    print(f"Steps: {train_steps}, Batch: {batch_size}, LR: {learning_rate}")
    print(f"LoRA rank: {lora_rank}, layers: {lora_layers}")
    print("-" * 60)

    # Run the training!
    # This is where the magic happens. Your Mac's GPU will heat up as it
    # processes thousands of examples from your articles.
    result = subprocess.run(cmd, cwd=str(cfg.PROJECT_ROOT))
    return result.returncode == 0


# =============================================================================
# POST-TRAINING: FUSE ADAPTERS WITH BASE MODEL
# =============================================================================

def fuse_adapters(
    base_model: str,
    adapter_path: Path,
    output_path: Path,
):
    """
    Fuse LoRA adapters with base model for inference.

    WHY FUSE?
    During training, we keep the adapters separate from the base model.
    For inference (actually using the model), we can "fuse" them together
    into a single model. This makes loading and running faster.

    Note: Fusing is optional. You can also load the base model + adapters
    separately, which is what we do by default.
    """
    cmd = [
        sys.executable, "-m", "mlx_lm.fuse",
        "--model", base_model,
        "--adapter-path", str(adapter_path),
        "--save-path", str(output_path),
    ]

    print(f"\nFusing adapters with base model...")
    result = subprocess.run(cmd, cwd=str(cfg.PROJECT_ROOT))
    return result.returncode == 0


# =============================================================================
# GGUF CONVERSION (For LM Studio)
# =============================================================================

def convert_to_gguf(
    mlx_model_path: Path,
    output_path: Path,
    quantization: str = "q4_k_m",
):
    """
    Convert MLX model to GGUF format for LM Studio.

    GGUF is the format used by llama.cpp and LM Studio. If you want to
    use your fine-tuned model in LM Studio (nice GUI), you'll need to
    convert it to GGUF format.

    This requires llama.cpp which is a separate tool. We just print
    instructions here since the setup is a bit involved.
    """
    print(f"\nTo convert to GGUF for LM Studio, use llama.cpp:")
    print(f"  1. Clone llama.cpp: git clone https://github.com/ggerganov/llama.cpp")
    print(f"  2. Run: python llama.cpp/convert_hf_to_gguf.py {mlx_model_path}")
    print(f"  3. Quantize: ./llama.cpp/llama-quantize model.gguf model-{quantization}.gguf {quantization}")
    print(f"\nAlternatively, use the fused MLX model directly with mlx_lm.generate")


# =============================================================================
# TEST THE FINE-TUNED MODEL
# =============================================================================

def test_generation(
    model_path: str,
    adapter_path: Optional[Path] = None,
    prompt: str = "Write a short article about Bitcoin.",
):
    """
    Test the fine-tuned model with a sample generation.

    This loads your fine-tuned model and generates a sample response
    to verify it's working and has learned your writing style.
    """
    print(f"\nTesting model generation...")

    try:
        if adapter_path and adapter_path.exists():
            # Load base model with LoRA adapters
            # This is the normal way to use a fine-tuned model
            model, tokenizer = load(
                model_path,
                adapter_path=str(adapter_path),
            )
        else:
            # Load model without adapters (base or fused)
            model, tokenizer = load(model_path)

        # Format the prompt using Phi-3's chat format
        # The model was trained to respond to this format
        formatted_prompt = f"<|user|>\n{cfg.STYLE_HINT}\n\n{prompt}<|end|>\n<|assistant|>\n"

        # Generate a response!
        # Temperature controls randomness (0.7 = slightly creative)
        # max_tokens limits response length
        response = generate(
            model,
            tokenizer,
            prompt=formatted_prompt,
            max_tokens=500,
            temp=0.7,
        )

        print("\n" + "=" * 60)
        print("Generated text:")
        print("=" * 60)
        print(response)
        print("=" * 60)

    except Exception as e:
        print(f"Error during generation: {e}")


# =============================================================================
# MAIN SCRIPT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Fine-tune Phi-3.5-mini with MLX LoRA")

    # Model settings
    parser.add_argument("--model", default=cfg.BASE_MODEL,
                        help="Base model to fine-tune (default: Phi-3.5-mini)")
    parser.add_argument("--data-dir", type=Path, default=cfg.DATASET_OUTPUT_DIR,
                        help="Training data directory")
    parser.add_argument("--output-dir", type=Path, default=cfg.PROJECT_ROOT / "fine_tuned_model",
                        help="Output directory for adapters")

    # Training hyperparameters (see docstrings above for explanations)
    parser.add_argument("--steps", type=int, default=cfg.MAX_STEPS,
                        help="Training steps (default: 1000)")
    parser.add_argument("--batch-size", type=int, default=cfg.BATCH_SIZE,
                        help="Batch size (default: 1, keep low for 24GB RAM)")
    parser.add_argument("--lr", type=float, default=cfg.LEARNING_RATE,
                        help="Learning rate (default: 0.0001)")
    parser.add_argument("--grad-accumulate", type=int, default=cfg.GRADIENT_ACCUMULATION,
                        help="Gradient accumulation steps")

    # LoRA settings
    parser.add_argument("--lora-rank", type=int, default=cfg.LORA_RANK,
                        help="LoRA rank (default: 16)")
    parser.add_argument("--lora-layers", type=int, default=16,
                        help="Number of LoRA layers")

    # Actions
    parser.add_argument("--resume", action="store_true",
                        help="Resume training from checkpoint")
    parser.add_argument("--fuse", action="store_true",
                        help="Fuse adapters with base model after training")
    parser.add_argument("--test", action="store_true",
                        help="Test generation after training")
    parser.add_argument("--test-only", action="store_true",
                        help="Only test existing model, don't train")
    parser.add_argument("--convert-gguf", action="store_true",
                        help="Show GGUF conversion instructions")

    args = parser.parse_args()

    # =========================================================================
    # TEST-ONLY MODE
    # =========================================================================
    # If you just want to test an already-trained model
    if args.test_only:
        adapter_path = args.output_dir / "adapters"
        if not adapter_path.exists():
            print(f"No adapters found at {adapter_path}")
            print("Run training first or specify a different output-dir")
            return
        test_generation(args.model, adapter_path)
        return

    # =========================================================================
    # CHECK TRAINING DATA
    # =========================================================================
    # Make sure we have training data before starting
    if not check_training_data(args.data_dir):
        print(f"\nTraining data not found at {args.data_dir}")
        print("Run: python prepare_medium_data.py --all")
        return

    # =========================================================================
    # RUN TRAINING
    # =========================================================================
    # This is the main event! Training can take 30-60 minutes depending on
    # the number of steps and your hardware.
    success = run_mlx_lm_lora(
        model=args.model,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        train_steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        lora_rank=args.lora_rank,
        lora_layers=args.lora_layers,
        grad_accumulate=args.grad_accumulate,
        resume=args.resume,
    )

    if not success:
        print("\nTraining failed. Check the error messages above.")
        return

    print("\nTraining complete!")
    print(f"Adapters saved to: {args.output_dir / 'adapters'}")

    # =========================================================================
    # POST-TRAINING OPTIONS
    # =========================================================================

    # Optionally fuse adapters with base model
    if args.fuse:
        fused_path = args.output_dir / "fused"
        fuse_adapters(args.model, args.output_dir / "adapters", fused_path)
        print(f"Fused model saved to: {fused_path}")

    # Optionally test the model
    if args.test:
        test_generation(args.model, args.output_dir / "adapters")

    # Show GGUF conversion instructions
    if args.convert_gguf:
        convert_to_gguf(args.output_dir / "fused", args.output_dir / "model.gguf")

    # Print next steps
    print("\nNext steps:")
    print("  1. Test: python finetune_mlx.py --test-only")
    print("  2. Fuse: python finetune_mlx.py --fuse")
    print("  3. Use in chat: python conor_ai.py chat")


if __name__ == "__main__":
    main()
