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


class FaissVectorStore:
    def __init__(self, persist_dir: Path):
        self.persist_dir = persist_dir
        self.index_path = self.persist_dir / "index.faiss"
        self.meta_path = self.persist_dir / "meta.json"
        self.entries: list[dict] = []
        self._index = None
        self._dim = None

    def _require_faiss(self):
        import faiss  # type: ignore
        import numpy as np

        return faiss, np

    def add_documents(self, documents: list[Document], embedding_client) -> None:
        faiss, np = self._require_faiss()
        vectors = []
        self.entries = []

        for document in documents:
            embedding = embedding_client.embed(document.page_content)
            dense = _dense_from_sparse_dict(embedding)
            if dense is None:
                continue

            vectors.append(dense)
            self.entries.append(
                {
                    "page_content": document.page_content,
                    "metadata": document.metadata,
                }
            )

        if not vectors:
            self._index = None
            self._dim = None
            self.persist()
            return

        matrix = np.array(vectors, dtype="float32")
        faiss.normalize_L2(matrix)

        self._dim = matrix.shape[1]
        self._index = faiss.IndexFlatIP(self._dim)
        self._index.add(matrix)
        self.persist()

    def persist(self) -> None:
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        if self._index is None:
            if self.index_path.exists():
                self.index_path.unlink()
            self.meta_path.write_text(
                json.dumps({"entries": self.entries, "dim": self._dim}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return

        faiss, _ = self._require_faiss()
        faiss.write_index(self._index, str(self.index_path))
        self.meta_path.write_text(
            json.dumps({"entries": self.entries, "dim": self._dim}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self) -> None:
        if not self.meta_path.exists() or not self.index_path.exists():
            self.entries = []
            self._index = None
            self._dim = None
            return

        faiss, _ = self._require_faiss()
        meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        self.entries = meta.get("entries", [])
        self._dim = meta.get("dim")
        self._index = faiss.read_index(str(self.index_path))

    def is_ready(self) -> bool:
        if self._index is None and self.index_path.exists() and self.meta_path.exists():
            self.load()
        return self._index is not None and bool(self.entries)

    def similarity_search(self, query: str, embedding_client, top_k: int = 3) -> list[dict]:
        if self._index is None:
            self.load()
        if self._index is None:
            return []

        _, np = self._require_faiss()
        query_embedding = embedding_client.embed(query)
        dense = _dense_from_sparse_dict(query_embedding)
        if dense is None:
            return []

        query_matrix = np.array([dense], dtype="float32")
        import faiss  # type: ignore

        faiss.normalize_L2(query_matrix)
        scores, indices = self._index.search(query_matrix, top_k)

        results = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0 or index >= len(self.entries):
                continue
            entry = self.entries[index]
            results.append(
                {
                    "page_content": entry["page_content"],
                    "metadata": entry["metadata"],
                    "score": float(score),
                }
            )
        return results


def create_vector_store(persist_dir: Path, backend: str = "simple"):
    normalized = backend.strip().lower()
    if normalized in {"faiss", "faiss-cpu"}:
        try:
            store = FaissVectorStore(persist_dir)
            store._require_faiss()
            return store, "faiss"
        except Exception:
            return SimpleVectorStore(persist_dir), "simple"
    return SimpleVectorStore(persist_dir), "simple"


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    return sum(left.get(token, 0.0) * right.get(token, 0.0) for token in left.keys())


def _dense_from_sparse_dict(values: dict[str, float]) -> list[float] | None:
    if not values:
        return None

    if not all(key.isdigit() for key in values.keys()):
        return None

    dim = max(int(key) for key in values.keys()) + 1
    dense = [0.0] * dim
    for key, value in values.items():
        dense[int(key)] = float(value)
    return dense
