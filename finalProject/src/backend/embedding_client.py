import math
import re
from collections import Counter

TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


class EmbeddingClient:
    def __init__(self, model_path: str, backend: str = "simple"):
        self.model_path = model_path
        self.model_name = "BGE-M3"
        self.backend = backend.strip().lower()
        self._simple_backend = _SimpleEmbeddingBackend()
        self._bge_backend = None
        self._active_backend = "simple"

        if self.backend in {"bge", "bge-m3", "sentence-transformers"}:
            candidate = _BGEM3EmbeddingBackend(model_path)
            if candidate.health():
                self._bge_backend = candidate
                self._active_backend = "bge-m3"

    @property
    def active_backend(self) -> str:
        return self._active_backend

    def embed(self, text: str) -> dict[str, float]:
        if self._bge_backend is not None:
            return self._bge_backend.embed(text)
        return self._simple_backend.embed(text)

    def health(self) -> bool:
        if self._bge_backend is not None:
            return self._bge_backend.health()
        return self._simple_backend.health()


class _SimpleEmbeddingBackend:
    def _tokenize(self, text: str) -> list[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text)]

    def embed(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}
        counts = Counter(tokens)
        norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
        return {token: value / norm for token, value in counts.items()}

    def health(self) -> bool:
        return True


class _BGEM3EmbeddingBackend:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model = None
        self._load_error = None
        self._try_load_model()

    def _try_load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_path)
        except Exception as exc:  # pragma: no cover - environment dependent
            self._model = None
            self._load_error = str(exc)

    def embed(self, text: str) -> dict[str, float]:
        if self._model is None:
            return {}

        vector = self._model.encode(text, normalize_embeddings=True)
        return {
            str(index): float(value)
            for index, value in enumerate(vector)
            if value != 0
        }

    def health(self) -> bool:
        return self._model is not None
