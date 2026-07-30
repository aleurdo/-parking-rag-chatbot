import re
from dataclasses import dataclass
from pathlib import Path

import markdown
from bs4 import BeautifulSoup


@dataclass
class DocumentChunk:
    content: str
    source: str
    chunk_id: str
    metadata: dict


def parse_markdown(file_path: Path) -> str:
    text = file_path.read_text(encoding="utf-8")
    html = markdown.markdown(text, extensions=["tables"])
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")


def split_by_headers(text: str, source: str) -> list[DocumentChunk]:
    sections = re.split(r"\n(?=#{1,3}\s)", text)
    chunks = []
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
        lines = section.split("\n", 1)
        title = lines[0].lstrip("#").strip() if lines else ""
        chunks.append(
            DocumentChunk(
                content=section,
                source=source,
                chunk_id=f"{source}::chunk_{i}",
                metadata={"title": title, "section_index": i},
            )
        )
    return chunks


def chunk_text(text: str, source: str, max_chars: int = 1000, overlap: int = 200) -> list[DocumentChunk]:
    header_chunks = split_by_headers(text, source)
    final_chunks = []
    for hc in header_chunks:
        if len(hc.content) <= max_chars:
            final_chunks.append(hc)
        else:
            sub_chunks = _split_long_chunk(hc, max_chars, overlap)
            final_chunks.extend(sub_chunks)
    return final_chunks


def _split_long_chunk(chunk: DocumentChunk, max_chars: int, overlap: int) -> list[DocumentChunk]:
    text = chunk.content
    parts = []
    start = 0
    part_idx = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            break_point = text.rfind("\n", start + 1, end)
            if break_point > start:
                end = break_point
        content = text[start:end].strip()
        if content:
            parts.append(
                DocumentChunk(
                    content=content,
                    source=chunk.source,
                    chunk_id=f"{chunk.chunk_id}_part_{part_idx}",
                    metadata={**chunk.metadata, "part": part_idx},
                )
            )
            part_idx += 1
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start
    return parts


def load_documents(docs_dir: Path) -> list[DocumentChunk]:
    all_chunks = []
    for md_file in sorted(docs_dir.glob("*.md")):
        text = parse_markdown(md_file)
        chunks = chunk_text(text, source=md_file.name)
        all_chunks.extend(chunks)
    return all_chunks
