import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from fastapi.testclient import TestClient

import app as backend_app

client = TestClient(backend_app.app)


def test_health_endpoint_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_status_endpoint_returns_expected_fields():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "backend" in data
    assert "index_ready" in data
    assert "qwen_ready" in data
    assert "embedding_backend" in data
    assert "vector_backend" in data
    assert "chain_backend" in data


def test_chat_without_index_returns_400(tmp_path, monkeypatch):
    backend_app.pipeline.vector_store.persist_dir = tmp_path
    backend_app.pipeline.vector_store.index_path = tmp_path / "index.json"
    backend_app.pipeline.vector_store.entries = []
    response = client.post("/api/chat", json={"question": "What is RAG?"})
    assert response.status_code == 400
    assert "Index not built" in response.json()["detail"]


class DummyStreamLLM:
    def health(self):
        return True

    def answer(self, prompt: str) -> str:
        return "stream fallback"

    def stream_answer(self, prompt: str):
        yield "RAG "
        yield "works"


def test_chat_stream_endpoint_returns_sse_payload(tmp_path, monkeypatch):
    backend_app.pipeline.vector_store.persist_dir = tmp_path
    backend_app.pipeline.vector_store.index_path = tmp_path / "index.json"
    backend_app.pipeline.vector_store.entries = [
        {
            "page_content": "RAG combines retrieval and generation.",
            "metadata": {"source": "intro.md"},
            "embedding": {"rag": 1.0},
        }
    ]
    backend_app.pipeline.llm_client = DummyStreamLLM()

    response = client.post("/api/chat/stream", json={"question": "What is RAG?"})
    assert response.status_code == 200
    assert '"type": "start"' in response.text
    assert '"type": "token"' in response.text
    assert '"type": "sources"' in response.text
    assert '"type": "done"' in response.text


def test_chat_endpoint_supports_stream_mode(tmp_path, monkeypatch):
    backend_app.pipeline.vector_store.persist_dir = tmp_path
    backend_app.pipeline.vector_store.index_path = tmp_path / "index.json"
    backend_app.pipeline.vector_store.entries = [
        {
            "page_content": "RAG combines retrieval and generation.",
            "metadata": {"source": "intro.md"},
            "embedding": {"rag": 1.0},
        }
    ]
    backend_app.pipeline.llm_client = DummyStreamLLM()

    response = client.post("/api/chat", json={"question": "What is RAG?"})
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/event-stream")
    assert '"type": "token"' in response.text


def test_chat_stream_alias_also_returns_sse(tmp_path, monkeypatch):
    backend_app.pipeline.vector_store.persist_dir = tmp_path
    backend_app.pipeline.vector_store.index_path = tmp_path / "index.json"
    backend_app.pipeline.vector_store.entries = [
        {
            "page_content": "RAG combines retrieval and generation.",
            "metadata": {"source": "intro.md"},
            "embedding": {"rag": 1.0},
        }
    ]
    backend_app.pipeline.llm_client = DummyStreamLLM()

    response = client.post("/api/chat/stream", json={"question": "What is RAG?"})
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/event-stream")
