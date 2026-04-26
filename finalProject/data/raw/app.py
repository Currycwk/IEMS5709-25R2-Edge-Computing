import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from loader import (
    list_external_code_projects,
    load_documents,
    load_external_code_project_documents,
    load_self_code_documents,
)
from rag_chain import pipeline


class ChatRequest(BaseModel):
    question: str
    top_k: int | None = Field(default=None, ge=1, le=10)
    corpus: str | None = Field(default=None)
    code_project: str | None = Field(default=None)


class BuildIndexRequest(BaseModel):
    corpus: str = Field(default="knowledge")
    code_project: str | None = Field(default=None)


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


@app.get("/api/corpora")
def corpora():
    return {
        "status": "ok",
        "available": ["knowledge", "self_code", "external_code"],
        "code_projects_dir": str(settings.code_projects_dir),
        "external_code_projects": list_external_code_projects(settings.code_projects_dir),
    }


@app.post("/api/index")
def build_index(request: BuildIndexRequest | None = None):
    selected_corpus = request.corpus if request else "knowledge"
    selected_project = request.code_project if request else None
    result = pipeline.build_index(corpus=selected_corpus, code_project=selected_project)
    return {"status": "ok", "message": "Index built successfully", **result}


@app.get("/api/documents")
def documents(corpus: str = "knowledge", code_project: str | None = None):
    corpus = (corpus or "knowledge").strip().lower()

    if corpus == "knowledge":
        docs = load_documents(settings.data_dir)
    elif corpus == "self_code":
        docs = load_self_code_documents(Path(__file__).resolve().parents[2])
    elif corpus == "external_code":
        docs = load_external_code_project_documents(settings.code_projects_dir, project_name=code_project)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported corpus: {corpus}")

    items = [
        {
            "source": doc.metadata.get("source", "unknown"),
            "path": doc.metadata.get("path", ""),
            "chars": len(doc.page_content),
            "preview": doc.page_content[:280],
            "content": doc.page_content,
            "doc_type": doc.metadata.get("doc_type", "unknown"),
            "page": doc.metadata.get("page"),
            "project": doc.metadata.get("project"),
            "language": doc.metadata.get("language"),
            "corpus": doc.metadata.get("corpus", corpus),
        }
        for doc in docs
    ]
    return {"status": "ok", "count": len(items), "corpus": corpus, "code_project": code_project, "documents": items}


def _build_stream_response(
    question: str,
    top_k: int | None = None,
    corpus: str | None = None,
    code_project: str | None = None,
) -> StreamingResponse:
    token_stream, sources = pipeline.chat_stream(
        question,
        top_k=top_k,
        corpus=corpus,
        code_project=code_project,
    )

    def event_generator():
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
        return _build_stream_response(
            request.question,
            top_k=request.top_k,
            corpus=request.corpus,
            code_project=request.code_project,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        return _build_stream_response(
            request.question,
            top_k=request.top_k,
            corpus=request.corpus,
            code_project=request.code_project,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/code/index/self")
def build_self_code_index():
    result = pipeline.build_index(corpus="self_code")
    return {"status": "ok", "message": "Self code index built", **result}


@app.post("/api/code/index/external/{project_name}")
def build_external_code_index(project_name: str):
    result = pipeline.build_index(corpus="external_code", code_project=project_name)
    return {"status": "ok", "message": f"External code index built: {project_name}", **result}


@app.post("/api/code/chat/self")
def chat_self_code(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return _build_stream_response(request.question, top_k=request.top_k, corpus="self_code")


@app.post("/api/code/chat/external/{project_name}")
def chat_external_code(project_name: str, request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return _build_stream_response(
        request.question,
        top_k=request.top_k,
        corpus="external_code",
        code_project=project_name,
    )


@app.get("/ui")
def ui():
    frontend_index = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    raise HTTPException(status_code=404, detail="Frontend not found")
