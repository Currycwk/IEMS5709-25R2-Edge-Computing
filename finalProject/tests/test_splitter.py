import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from loader import Document
from splitter import split_documents


def test_split_documents_creates_multiple_chunks():
    docs = [Document(page_content="a" * 1200, metadata={"source": "x.txt"})]
    chunks = split_documents(docs, chunk_size=300, chunk_overlap=50)
    assert len(chunks) >= 4
    assert all(chunk.metadata["source"] == "x.txt" for chunk in chunks)


def test_split_documents_invalid_overlap_raises():
    docs = [Document(page_content="hello", metadata={})]
    try:
        split_documents(docs, chunk_size=100, chunk_overlap=100)
        assert False, "Expected ValueError"
    except ValueError:
        assert True
