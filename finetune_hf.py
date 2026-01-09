# finetune_hf.py  (no Unsloth)
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_from_disk

BASE = "google/gemma-3-270m"
DATA = "my_medium_dataset_all"

tok = AutoTokenizer.from_pretrained(BASE)
tok.pad_token = tok.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE,
    torch_dtype="auto",
    device_map=None,     # CPU
)

# LoRA config
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

# Load your dataset and join into a single 'text' field
ds = load_from_disk(DATA)
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

args = TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=10,
    max_steps=200,       # raise later (e.g., 800–1500) for stronger fit
    learning_rate=2e-4,
    fp16=False,
    logging_steps=10,
    output_dir="my_personal_ai",
    save_strategy="no",
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tok,
    train_dataset=ds,
    dataset_text_field="text",
    max_seq_length=2048,
    args=args,
)
trainer.train()

# Merge LoRA and save standard HF model
model = model.merge_and_unload()
model.save_pretrained("my_personal_ai_model")
tok.save_pretrained("my_personal_ai_model")
print("✅ Saved HF model to my_personal_ai_model/")
