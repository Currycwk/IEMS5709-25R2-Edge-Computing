import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from fastapi.testclient import TestClient

import app as backend_app
from vector_store import SimpleVectorStore

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


def test_delete_external_code_project_removes_directory_and_clears_active_index(tmp_path, monkeypatch):
    code_projects_dir = tmp_path / "code_projects"
    project_dir = code_projects_dir / "demo_project"
    project_dir.mkdir(parents=True)
    (project_dir / "main.py").write_text("print('hello')", encoding="utf-8")

    monkeypatch.setattr(backend_app.settings, "code_projects_dir", code_projects_dir)

    vector_store = SimpleVectorStore(tmp_path / "vector_db")
    vector_store.entries = [
        {
            "page_content": "print('hello')",
            "metadata": {"source": "demo_project/main.py"},
            "embedding": {"hello": 1.0},
        }
    ]
    vector_store.persist()
    monkeypatch.setattr(backend_app.pipeline, "vector_store", vector_store)
    backend_app.pipeline.active_corpus = "external_code"
    backend_app.pipeline.active_code_project = "demo_project"

    response = client.request("DELETE", "/api/code/external/demo_project")
    assert response.status_code == 200

    data = response.json()
    assert data["project_name"] == "demo_project"
    assert data["cleared_active_index"] is True
    assert data["remaining_projects"] == []
    assert not project_dir.exists()
    assert backend_app.pipeline.active_code_project is None
    assert backend_app.pipeline.active_corpus == "knowledge"
    assert backend_app.pipeline.vector_store.is_ready() is False


def test_delete_knowledge_document_removes_file_and_clears_active_index(tmp_path, monkeypatch):
    data_dir = tmp_path / "raw"
    data_dir.mkdir(parents=True)
    knowledge_file = data_dir / "notes.md"
    knowledge_file.write_text("RAG notes", encoding="utf-8")

    monkeypatch.setattr(backend_app.settings, "data_dir", data_dir)

    vector_store = SimpleVectorStore(tmp_path / "vector_db")
    vector_store.entries = [
        {
            "page_content": "RAG notes",
            "metadata": {"source": "notes.md"},
            "embedding": {"rag": 1.0},
        }
    ]
    vector_store.persist()
    monkeypatch.setattr(backend_app.pipeline, "vector_store", vector_store)
    backend_app.pipeline.active_corpus = "knowledge"
    backend_app.pipeline.active_code_project = None

    response = client.request("DELETE", f"/api/knowledge/document?path={knowledge_file}")
    assert response.status_code == 200

    data = response.json()
    assert data["cleared_active_index"] is True
    assert data["remaining_documents"] == 0
    assert not knowledge_file.exists()
    assert backend_app.pipeline.active_corpus == "knowledge"
    assert backend_app.pipeline.vector_store.is_ready() is False


def test_upload_knowledge_document_accepts_supported_type_and_rebuilds_index(tmp_path, monkeypatch):
    data_dir = tmp_path / "raw"
    data_dir.mkdir(parents=True)
    monkeypatch.setattr(backend_app.settings, "data_dir", data_dir)

    class DummyPipeline:
        def build_index(self, corpus="knowledge", code_project=None):
            assert corpus == "knowledge"
            return {"documents": 1, "chunks": 1, "index_ready": True, "doc_types": {"md": 1}, "corpus": "knowledge", "code_project": None}

    monkeypatch.setattr(backend_app, "pipeline", DummyPipeline())

    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("notes.md", b"# RAG Notes", "text/markdown")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "notes.md"
    assert (data_dir / "notes.md").exists()
    assert data["documents"] == 1


def test_upload_knowledge_document_rejects_unsupported_type(tmp_path, monkeypatch):
    data_dir = tmp_path / "raw"
    data_dir.mkdir(parents=True)
    monkeypatch.setattr(backend_app.settings, "data_dir", data_dir)

    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("notes.docx", b"binary", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 400
    assert "Only these file types are supported" in response.json()["detail"]


def test_upload_knowledge_document_rejects_duplicate_filename(tmp_path, monkeypatch):
    data_dir = tmp_path / "raw"
    data_dir.mkdir(parents=True)
    (data_dir / "notes.md").write_text("existing", encoding="utf-8")
    monkeypatch.setattr(backend_app.settings, "data_dir", data_dir)

    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("notes.md", b"# New Notes", "text/markdown")},
    )
    assert response.status_code == 409
    assert "Knowledge document already exists" in response.json()["detail"]
