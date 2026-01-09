# finetune.py
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_from_disk

DATA_DIR = "my_medium_dataset_all"  # your prepared dataset folder

# 1) base model
model, tokenizer = FastLanguageModel.from_pretrained(
    "google/gemma-3-270m",
    max_seq_length=2048,
    dtype=None,          # auto
    load_in_4bit=False,  # CPU-friendly; 270M is tiny
)

# 2) LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing=True,
)

# 3) dataset -> join fields into one 'text'
ds = load_from_disk(DATA_DIR)
def to_text(batch):
    texts = []
    for inst, inp, out in zip(batch["instruction"], batch["input"], batch["output"]):
        texts.append(
            "### Instruction:\n"
            + inst + "\n\n### Input:\n"
            + inp + "\n\n### Output:\n"
            + out
        )
    return {"text": texts}
ds = ds.map(to_text, batched=True, remove_columns=list(ds.features.keys()))

# 4) train
args = TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=10,
    max_steps=200,      # raise later (e.g., 800–1500) for stronger fit
    learning_rate=2e-4,
    fp16=False,         # CPU
    logging_steps=10,
    output_dir="my_personal_ai",
    save_strategy="no",
)
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=ds,
    dataset_text_field="text",
    max_seq_length=2048,
    args=args,
)
trainer.train()

# 5) save HF + GGUF
model.save_pretrained_merged("my_personal_ai_model", tokenizer, save_method="merged_16bit")
model.save_pretrained_gguf("my_personal_ai_gguf", tokenizer, quantization_method="q8_0")
print("✅ Done: my_personal_ai_model/ and my_personal_ai_gguf/")
