import tempfile
from pathlib import Path

import pytest

from app.rag.chunker import (
    DocumentChunk,
    chunk_text,
    load_documents,
    parse_markdown,
    split_by_headers,
)


@pytest.fixture
def sample_markdown(tmp_path):
    content = """# Title

Some introduction text here.

## Section One

Content for section one with details.

## Section Two

Content for section two with more details.
This section has multiple lines.
And continues here.
"""
    md_file = tmp_path / "test.md"
    md_file.write_text(content)
    return md_file


def test_parse_markdown(sample_markdown):
    text = parse_markdown(sample_markdown)
    assert "Title" in text
    assert "Section One" in text
    assert "Content for section one" in text


def test_split_by_headers():
    text = "# Main\nIntro\n## Sub1\nContent1\n## Sub2\nContent2"
    chunks = split_by_headers(text, "test.md")
    assert len(chunks) >= 2
    assert all(isinstance(c, DocumentChunk) for c in chunks)
    assert chunks[0].source == "test.md"


def test_chunk_text_respects_max_chars():
    long_text = "# Header\n" + "A" * 2000
    chunks = chunk_text(long_text, "test.md", max_chars=500)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.content) <= 600  # some tolerance for overlap


def test_chunk_text_short_content():
    short_text = "# Header\nShort content here."
    chunks = chunk_text(short_text, "test.md", max_chars=1000)
    assert len(chunks) == 1
    assert "Short content" in chunks[0].content


def test_load_documents(tmp_path):
    (tmp_path / "doc1.md").write_text("# Doc1\nContent one.")
    (tmp_path / "doc2.md").write_text("# Doc2\nContent two.")
    (tmp_path / "ignored.txt").write_text("Not markdown")

    chunks = load_documents(tmp_path)
    assert len(chunks) >= 2
    sources = {c.source for c in chunks}
    assert "doc1.md" in sources
    assert "doc2.md" in sources
    assert "ignored.txt" not in sources


def test_chunk_ids_are_unique():
    text = "# A\nContent A\n## B\nContent B\n## C\nContent C"
    chunks = chunk_text(text, "test.md")
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
