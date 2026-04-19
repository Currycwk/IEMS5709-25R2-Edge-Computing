import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from loader import load_documents


def test_load_documents_reads_txt_and_md(tmp_path):
    (tmp_path / "a.txt").write_text("hello world", encoding="utf-8")
    (tmp_path / "b.md").write_text("# title", encoding="utf-8")
    documents = load_documents(tmp_path)
    assert len(documents) == 2
    assert {doc.metadata['source'] for doc in documents} == {"a.txt", "b.md"}


def test_load_documents_ignores_other_extensions(tmp_path):
    (tmp_path / "a.pdf").write_text("ignored", encoding="utf-8")
    documents = load_documents(tmp_path)
    assert documents == []
