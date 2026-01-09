# finetune_plain.py — no TRL, uses plain transformers.Trainer
import os
from datasets import load_from_disk
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

BASE = "google/gemma-3-270m"
DATA = "my_medium_dataset_all"
MAX_LEN = 2048

# 1) tokenizer & model
tok = AutoTokenizer.from_pretrained(BASE)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE,
    torch_dtype="auto",
    device_map=None,   # CPU
)

# 2) LoRA
peft_cfg = LoraConfig(
    r=16,
    lora_alpha=16,
    lora_dropout=0.0,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)
model = prepare_model_for_kbit_training(model)  # harmless on CPU
model = get_peft_model(model, peft_cfg)

# 3) load dataset and build a single text field
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

# 4) tokenize (no padding here; let collator handle dynamic padding)
def tok_fn(examples):
    return tok(examples["text"], truncation=True, max_length=MAX_LEN)

tokenized = ds.map(tok_fn, batched=True, remove_columns=["text"])

# 5) data collator to create labels = input_ids (causal LM)
collator = DataCollatorForLanguageModeling(tokenizer=tok, mlm=False)

# 6) training args
args = TrainingArguments(
    output_dir="my_personal_ai",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=10,
    max_steps=200,          # increase later (e.g., 800–1500) for stronger fit
    logging_steps=10,
    save_strategy="no",
    fp16=False,             # CPU
)

# 7) train
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized,
    data_collator=collator,
)
trainer.train()

# 8) merge LoRA and save standard HF format
model = model.merge_and_unload()
os.makedirs("my_personal_ai_model", exist_ok=True)
model.save_pretrained("my_personal_ai_model")
tok.save_pretrained("my_personal_ai_model")

print("✅ Saved HF model to my_personal_ai_model/")
