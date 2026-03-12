## ASR Model

```bash
docker run -it \
  --runtime nvidia \
  --rm \
  -p 8880:8880 \
  dustynv/kokoro-tts:fastapi-r36.4.0-cu128-24.04

python test.py
```

The synthesized audio file is saved in `kokoro-tts-fastapi/kokoro-af_heart-fastapi.mp3`.

## TTS Server

```bash
docker run \
  --runtime nvidia \
  --rm \
  --network=host \
  -v $PWD/faster-whisper:/workspace \
  dustynv/faster-whisper:r36.4.0-cu128-24.04 \
  bash -c "cd /workspace && python test.py"
```

You can see the transcription result of `faster-whisper/asr_en.wav` in the terminal.