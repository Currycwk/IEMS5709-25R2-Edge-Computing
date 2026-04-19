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


def test_chat_without_index_returns_400(tmp_path, monkeypatch):
    backend_app.pipeline.vector_store.persist_dir = tmp_path
    backend_app.pipeline.vector_store.index_path = tmp_path / "index.json"
    backend_app.pipeline.vector_store.entries = []
    response = client.post("/api/chat", json={"question": "What is RAG?"})
    assert response.status_code == 400
    assert "Index not built" in response.json()["detail"]
