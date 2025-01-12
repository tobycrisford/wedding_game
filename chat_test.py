import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from prompts import system_prompt

model_id = "unsloth/Llama-3.2-3B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
)

# Load model with quantization
model = AutoModelForCausalLM.from_pretrained(
    model_id,
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

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "Hi, what's your name?"},
]

while True:

    output = pipe(messages, max_new_tokens=1024)
    response = output[0]['generated_text'][-1]['content']
    messages.append({"role": "agent", "content": response})
    print("Agent: ", response)
    user_msg = input("User: ")
    messages.append({"role": "user", "content": user_msg})
