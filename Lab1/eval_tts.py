import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel


device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

print(f"Using device: {device}")
print(f"Using dtype: {dtype}")

model = Qwen3TTSModel.from_pretrained(
    "Qwen3-TTS-12Hz-0.6B-Base",
    dtype=dtype,
    device_map=device,
)

# Reference audio: your own voice
ref_audio = "resources/clone.wav"

# Reference text: read from clone.txt
with open("clone.txt", "r", encoding="utf-8") as f:
    ref_text = f.read().strip()

# Text to be generated (will also be saved to tts.txt)
tts_text = (
    "这是我在香港中文大学读书期间录制的一段测试语音，"
    "用于完成 IEMS5709 课程的语音合成实验。"
)

with open("tts.txt", "w", encoding="utf-8") as f:
    f.write(tts_text + "\n")

wavs, sr = model.generate_voice_clone(
    text=tts_text,
    language="Chinese",
    ref_audio=ref_audio,
    ref_text=ref_text,
)

sf.write("tts.wav", wavs[0], sr)

