import json
import math
from pathlib import Path

from loader import Document


class SimpleVectorStore:
    def __init__(self, persist_dir: Path):
        self.persist_dir = persist_dir
        self.index_path = self.persist_dir / "index.json"
        self.entries: list[dict] = []

    def add_documents(self, documents: list[Document], embedding_client) -> None:
        self.entries = []
        for document in documents:
            embedding = embedding_client.embed(document.page_content)
            self.entries.append(
                {
                    "page_content": document.page_content,
                    "metadata": document.metadata,
                    "embedding": embedding,
                }
            )
        self.persist()

    def persist(self) -> None:
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(self.entries, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> None:
        if self.index_path.exists():
            self.entries = json.loads(self.index_path.read_text(encoding="utf-8"))
        else:
            self.entries = []

    def is_ready(self) -> bool:
        if not self.entries and self.index_path.exists():
            self.load()
        return bool(self.entries)

    def similarity_search(self, query: str, embedding_client, top_k: int = 3) -> list[dict]:
        if not self.entries:
            self.load()
        query_embedding = embedding_client.embed(query)
        scored = []
        for entry in self.entries:
            score = cosine_similarity(query_embedding, entry.get("embedding", {}))
            scored.append({
                "page_content": entry["page_content"],
                "metadata": entry["metadata"],
                "score": score,
            })
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    return sum(left.get(token, 0.0) * right.get(token, 0.0) for token in left.keys())
