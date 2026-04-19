import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from embedding_client import EmbeddingClient
from loader import Document
from vector_store import SimpleVectorStore


def test_vector_store_similarity_search(tmp_path):
    store = SimpleVectorStore(tmp_path)
    embedding = EmbeddingClient("/tmp/bge-m3")
    documents = [
        Document(page_content="RAG combines retrieval and generation", metadata={"source": "intro.md"}),
        Document(page_content="Docker Compose orchestrates local services", metadata={"source": "deploy.txt"}),
    ]
    store.add_documents(documents, embedding)
    results = store.similarity_search("What is retrieval augmented generation", embedding, top_k=1)
    assert len(results) == 1
    assert results[0]["metadata"]["source"] == "intro.md"
