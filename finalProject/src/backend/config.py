import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent


@dataclass
class Settings:
    qwen_base_url: str = os.getenv("QWEN_BASE_URL", "http://localhost:8000/v1")
    qwen_model: str = os.getenv("QWEN_MODEL", "/root/.cache/huggingface/Qwen3-4B-quantized.w4a16")
    embedding_model_path: str = os.getenv("EMBEDDING_MODEL_PATH", "/opt/models/bge-m3")
    embedding_backend: str = os.getenv("EMBEDDING_BACKEND", "simple")
    vector_db_dir: Path = Path(os.getenv("VECTOR_DB_DIR", str(PROJECT_ROOT / "vector_db")))
    vector_backend: str = os.getenv("VECTOR_BACKEND", "simple")
    data_dir: Path = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data" / "raw")))
    top_k: int = int(os.getenv("TOP_K", "3"))
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8001"))


settings = Settings()
