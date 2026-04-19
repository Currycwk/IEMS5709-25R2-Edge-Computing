from loader import Document


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
        text = doc.page_content
        start = 0
        chunk_index = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunk_text = text[start:end].strip()
            if chunk_text:
                metadata = dict(doc.metadata)
                metadata["chunk_index"] = chunk_index
                chunks.append(Document(page_content=chunk_text, metadata=metadata))
            if end >= len(text):
                break
            start += step
            chunk_index += 1

    return chunks
