import torch
from qwen_asr import Qwen3ASRModel

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

print(f"Using device: {device}")
print(f"Using dtype: {dtype}")

model = Qwen3ASRModel.from_pretrained(
    "Qwen3-ASR-0.6B",
    dtype=dtype,
    device_map=device,
    max_inference_batch_size=4,
    max_new_tokens=256,
)

results = model.transcribe(
    audio="resources/asr.wav",
    language=None, # set "English" to force the language
)

language = results[0].language
text = results[0].text

with open("asr.txt", "w", encoding="utf-8") as f:
    f.write(f"{language}\n{text}\n")

print(language)
print(text)