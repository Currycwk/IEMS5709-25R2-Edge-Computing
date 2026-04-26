import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent


@dataclass
class Settings:
    llm_mode: str = os.getenv("LLM_MODE", "local")
    qwen_base_url: str = os.getenv("QWEN_BASE_URL", "http://localhost:8000/v1")
    qwen_model: str = os.getenv("QWEN_MODEL", "/root/.cache/huggingface/Qwen3-4B-quantized.w4a16")
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_health_path: str = os.getenv("QWEN_HEALTH_PATH", "/models")
    local_max_tokens: int = int(os.getenv("LOCAL_MAX_TOKENS", "2048"))
    api_max_tokens: int = int(os.getenv("API_MAX_TOKENS", "2048"))
    embedding_model_path: str = os.getenv("EMBEDDING_MODEL_PATH", "/opt/models/bge-m3")
    embedding_backend: str = os.getenv("EMBEDDING_BACKEND", "simple")
    vector_db_dir: Path = Path(os.getenv("VECTOR_DB_DIR", str(PROJECT_ROOT / "vector_db")))
    vector_backend: str = os.getenv("VECTOR_BACKEND", "simple")
    data_dir: Path = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data" / "raw")))
    code_projects_dir: Path = Path(os.getenv("CODE_PROJECTS_DIR", str(PROJECT_ROOT / "data" / "code_projects")))
    top_k: int = int(os.getenv("TOP_K", "3"))
    retrieval_fetch_k: int = int(os.getenv("RETRIEVAL_FETCH_K", "8"))
    retrieval_strategy: str = os.getenv("RETRIEVAL_STRATEGY", "hybrid")
    expand_adjacent_chunks: bool = os.getenv("EXPAND_ADJACENT_CHUNKS", "true").strip().lower() in {"1", "true", "yes", "on"}
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8001"))


settings = Settings()
