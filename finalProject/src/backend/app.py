import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import settings
from rag_chain import pipeline


class ChatRequest(BaseModel):
    question: str


app = FastAPI(title="Local RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Local RAG backend is running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    return pipeline.status()


@app.post("/api/index")
def build_index():
    result = pipeline.build_index()
    return {"status": "ok", "message": "Index built successfully", **result}


def _build_stream_response(question: str) -> StreamingResponse:
    token_stream, sources = pipeline.chat_stream(question)

    def event_generator():
        # Kick off early to reduce buffering in browsers/proxies.
        yield "data: {\"type\": \"start\"}\n\n"

        try:
            for token in token_stream:
                payload = {"type": "token", "token": token}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except Exception as exc:
            error_payload = {"type": "error", "message": str(exc)}
            yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"

        sources_payload = {"type": "sources", "sources": sources}
        yield f"data: {json.dumps(sources_payload, ensure_ascii=False)}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


@app.post("/api/chat")
def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        return _build_stream_response(request.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        return _build_stream_response(request.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/ui")
def ui():
    frontend_index = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    raise HTTPException(status_code=404, detail="Frontend not found")
