from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Document:
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_documents(data_dir: Path) -> list[Document]:
    documents: list[Document] = []
    if not data_dir.exists():
        return documents

    for path in sorted(data_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": path.name, "path": str(path)},
                    )
                )
    return documents
