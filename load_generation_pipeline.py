import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"

def load_pipeline():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
    )

    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    return pipe


if __name__ == '__main__':
    # Used to initialize HF cache on docker build
    pipe = load_pipeline()