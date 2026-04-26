import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Document:
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".md"}
IGNORED_CODE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".cursor", "vector_db", "data"}
MAX_CODE_FILE_CHARS = 12000


def load_documents(data_dir: Path) -> list[Document]:
    documents: list[Document] = []
    if not data_dir.exists():
        return documents

    for path in sorted(data_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            text = _clean_text(path.read_text(encoding="utf-8", errors="ignore"))
            if text:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": path.name,
                            "path": str(path),
                            "source_doc_id": str(path),
                            "doc_type": suffix.lstrip("."),
                            "corpus": "knowledge",
                        },
                    )
                )
            continue

        if suffix == ".pdf":
            documents.extend(_load_pdf_documents(path))

    return documents


def _is_ignored_under_root(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        rel_parts = path.parts
    return any(part in IGNORED_CODE_DIRS for part in rel_parts)


def load_self_code_documents(project_root: Path) -> list[Document]:
    include_roots = [project_root / "src", project_root / "README.md", project_root / "docker-compose.yaml"]
    docs: list[Document] = []

    for entry in include_roots:
        if entry.is_file():
            docs.extend(_load_code_file(entry, project_root, project_name="self"))
        elif entry.is_dir():
            for path in sorted(entry.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in CODE_EXTENSIONS:
                    continue
                if _is_ignored_under_root(path, project_root):
                    continue
                docs.extend(_load_code_file(path, project_root, project_name="self"))

    return docs


def load_external_code_project_documents(code_projects_dir: Path, project_name: str | None = None) -> list[Document]:
    if not code_projects_dir.exists() or not code_projects_dir.is_dir():
        return []

    if project_name:
        target = code_projects_dir / project_name
        if not target.exists() or not target.is_dir():
            return []
        roots = [target]
    else:
        roots = [p for p in sorted(code_projects_dir.iterdir()) if p.is_dir()]

    docs: list[Document] = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            if _is_ignored_under_root(path, root):
                continue
            docs.extend(_load_code_file(path, root.parent, project_name=root.name))

    return docs


def list_external_code_projects(code_projects_dir: Path) -> list[str]:
    if not code_projects_dir.exists() or not code_projects_dir.is_dir():
        return []
    return [p.name for p in sorted(code_projects_dir.iterdir()) if p.is_dir()]


def _load_pdf_documents(path: Path) -> list[Document]:
    try:
        from pypdf import PdfReader
    except Exception:
        return []

    docs: list[Document] = []

    try:
        reader = PdfReader(str(path))
    except Exception:
        return docs

    for page_index, page in enumerate(reader.pages):
        try:
            raw_text = page.extract_text() or ""
        except Exception:
            raw_text = ""

        text = _clean_text(raw_text)
        if not text:
            continue

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": path.name,
                    "path": str(path),
                    "source_doc_id": str(path),
                    "doc_type": "pdf",
                    "page": page_index + 1,
                    "corpus": "knowledge",
                },
            )
        )

    return docs


def _load_code_file(path: Path, base_root: Path, project_name: str) -> list[Document]:
    text = _clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    if not text:
        return []

    truncated = False
    if len(text) > MAX_CODE_FILE_CHARS:
        head = text[: int(MAX_CODE_FILE_CHARS * 0.65)]
        tail = text[-int(MAX_CODE_FILE_CHARS * 0.35):]
        text = f"{head}\n\n... [TRUNCATED FOR INDEXING PERFORMANCE] ...\n\n{tail}"
        truncated = True

    rel_path = path.relative_to(base_root).as_posix() if path.is_relative_to(base_root) else path.name
    return [
        Document(
            page_content=text,
            metadata={
                "source": rel_path,
                "path": str(path),
                "source_doc_id": str(path),
                "doc_type": "code",
                "language": path.suffix.lower().lstrip("."),
                "project": project_name,
                "corpus": "code",
                "truncated": truncated,
            },
        )
    ]


def _clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t\f\v]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()
