# finetune_fast.py — Mac-safe, faster, no multiprocessing spawn issues
import os, torch
from datasets import load_from_disk
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    Trainer, TrainingArguments,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# --- tame thread warnings / stalls ---
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.0")
torch.set_float32_matmul_precision("high")

BASE = "google/gemma-3-270m"
DATA = "my_medium_dataset_all"
MAX_LEN = 1024  # lower = faster; can raise later

def main():
    tok = AutoTokenizer.from_pretrained(BASE)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE,
        torch_dtype="float32",        # MPS prefers fp32
        device_map="auto",            # use MPS if available; else CPU
        attn_implementation="eager",  # Gemma 3 recommendation
    )

    # LoRA
    peft_cfg = LoraConfig(
        r=16, lora_alpha=16, lora_dropout=0.0,
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
        bias="none", task_type="CAUSAL_LM",
    )
    model = prepare_model_for_kbit_training(model)  # harmless on CPU/MPS
    model = get_peft_model(model, peft_cfg)

    # Dataset -> join to one text field
    ds = load_from_disk(DATA)
    def join_fields(batch):
        out = []
        for inst, inp, tgt in zip(batch["instruction"], batch["input"], batch["output"]):
            out.append(
                "### Instruction:\n" + inst +
                "\n\n### Input:\n" + inp +
                "\n\n### Output:\n" + tgt
            )
        return {"text": out}
    ds = ds.map(join_fields, batched=True, remove_columns=list(ds.features.keys()))

    # Tokenize
    def tok_fn(examples):
        return tok(examples["text"], truncation=True, max_length=MAX_LEN)
    tokenized = ds.map(tok_fn, batched=True, remove_columns=["text"])

    collator = DataCollatorForLanguageModeling(tokenizer=tok, mlm=False)

    args = TrainingArguments(
        output_dir="my_personal_ai_fast",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,    # smaller = faster step
        learning_rate=2e-4,
        warmup_steps=10,
        max_steps=200,                    # raise later for quality
        logging_steps=10,
        save_strategy="no",
        fp16=False, bf16=False,           # MPS doesn’t use fp16 here
        dataloader_num_workers=0,         # <<< key: no multiprocessing
        dataloader_pin_memory=False,      # silence pin warning
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized,
        data_collator=collator,
    )
    trainer.train()

    # Merge LoRA and save HF model
    model = model.merge_and_unload()
    model.save_pretrained("my_personal_ai_model")
    tok.save_pretrained("my_personal_ai_model")
    print("✅ Saved HF model to my_personal_ai_model/")

if __name__ == "__main__":
    main()
