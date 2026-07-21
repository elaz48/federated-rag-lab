"""Document loading and chunking helpers shared by stages."""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Defaults match the plan: ~500 chars with small overlap so adjacent chunks
# still share a sentence or two without blowing context.
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


def repo_root() -> Path:
    """Return the repository root (parent of common/)."""
    return Path(__file__).resolve().parent.parent


def docs_dir() -> Path:
    return repo_root() / "data" / "docs"


def load_markdown_docs(directory: Path | None = None) -> list[Document]:
    """Load every *.md file under data/docs as a LangChain Document.

    Metadata keeps the source filename so later stages can show the reader
    which file a chunk came from.
    """
    path = directory or docs_dir()
    if not path.is_dir():
        raise FileNotFoundError(f"Docs directory not found: {path}")

    documents: list[Document] = []
    for md_file in sorted(path.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        documents.append(
            Document(
                page_content=text,
                metadata={"source": md_file.name},
            )
        )
    if not documents:
        raise FileNotFoundError(f"No markdown files found in {path}")
    return documents


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """Split documents with a simple recursive character splitter.

    RecursiveCharacterTextSplitter tries paragraph/sentence boundaries before
    hard mid-word cuts — good enough for short teaching docs without a custom
    markdown-aware splitter.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(documents)
