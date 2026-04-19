import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from fastapi.testclient import TestClient

import app as backend_app

client = TestClient(backend_app.app)


class DummyLLM:
    def health(self):
        return True

    def answer(self, prompt: str) -> str:
        return "Answer for: What is RAG?"


def test_end_to_end_index_then_chat(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "kb.txt").write_text(
        "RAG uses retrieval and generation together.", encoding="utf-8"
    )

    backend_app.settings.data_dir = data_dir
    backend_app.pipeline.vector_store.persist_dir = tmp_path / "vector_db"
    backend_app.pipeline.vector_store.index_path = backend_app.pipeline.vector_store.persist_dir / "index.json"
    backend_app.pipeline.vector_store.entries = []
    backend_app.pipeline.llm_client = DummyLLM()

    index_response = client.post("/api/index")
    assert index_response.status_code == 200

    chat_response = client.post("/api/chat", json={"question": "What is RAG?"})
    assert chat_response.status_code == 200
    data = chat_response.json()
    assert data["answer"] == "Answer for: What is RAG?"
    assert len(data["sources"]) >= 1
