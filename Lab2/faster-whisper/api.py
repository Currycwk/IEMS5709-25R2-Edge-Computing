"""
OpenAI-compatible ASR API using faster-whisper (persistent FastAPI service).
"""

from __future__ import annotations

import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel

MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small.en")
BEAM_SIZE = int(os.environ.get("WHISPER_BEAM_SIZE", "5"))
ALLOWED_MODEL_IDS = frozenset({"faster-whisper", "whisper-1"})

_whisper: WhisperModel | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _whisper
    _whisper = WhisperModel(
        MODEL_SIZE,
        device="cuda",
        compute_type=os.environ.get("WHISPER_COMPUTE_TYPE", "int8_float16"),
    )
    yield
    _whisper = None


app = FastAPI(title="Faster-Whisper ASR", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/models")
def list_models():
    import time

    return {
        "object": "list",
        "data": [
            {
                "id": "faster-whisper",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
            }
        ],
    }


@app.post("/v1/audio/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    model: str = Form("faster-whisper"),
):
    if _whisper is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if model not in ALLOWED_MODEL_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {model!r}. Use 'faster-whisper'.",
        )

    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            body = await file.read()
            tmp.write(body)
            tmp_path = tmp.name

        segments, _info = _whisper.transcribe(tmp_path, beam_size=BEAM_SIZE)
        text = "".join(segment.text for segment in segments).strip()
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return JSONResponse(content={"text": text})
