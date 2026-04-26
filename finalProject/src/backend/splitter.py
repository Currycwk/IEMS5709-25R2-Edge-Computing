import re

from loader import Document

SENTENCE_BREAK_RE = re.compile(r"(?<=[。！？.!?])\s+")


def split_documents(
    documents: list[Document],
    chunk_size: int = 1200,
    chunk_overlap: int = 150,
) -> list[Document]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be between 0 and chunk_size - 1")

    chunks: list[Document] = []
    step = chunk_size - chunk_overlap

    for doc in documents:
        text = _normalize_for_split(doc.page_content)
        if not text:
            continue

        windows = _sentence_aware_windows(text, chunk_size=chunk_size, step=step)
        for chunk_index, chunk_text in enumerate(windows):
            if not chunk_text:
                continue
            metadata = dict(doc.metadata)
            metadata["chunk_index"] = chunk_index
            chunks.append(Document(page_content=chunk_text, metadata=metadata))

    return chunks


def _normalize_for_split(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _sentence_aware_windows(text: str, chunk_size: int, step: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    windows: list[str] = []
    start = 0

    while start < len(text):
        ideal_end = min(len(text), start + chunk_size)
        end = _nearest_sentence_end(text, start, ideal_end)
        chunk_text = text[start:end].strip()
        if chunk_text:
            windows.append(chunk_text)

        if end >= len(text):
            break

        start = max(0, end - (chunk_size - step))
        if start >= len(text):
            break

    return windows


def _nearest_sentence_end(text: str, start: int, ideal_end: int) -> int:
    if ideal_end >= len(text):
        return len(text)

    probe = text[start:ideal_end + 120]
    matches = list(SENTENCE_BREAK_RE.finditer(probe))
    if not matches:
        newline_pos = probe.rfind("\n")
        if newline_pos > int(len(probe) * 0.6):
            return start + newline_pos + 1
        return ideal_end

    best = None
    target = ideal_end - start
    for m in matches:
        pos = m.end()
        if pos < int(target * 0.6):
            continue
        best = pos
        break

    if best is None:
        best = matches[-1].end()

    return min(len(text), start + best)
