"""Index Meridian docs into a local Chroma collection.

Run from the repo root:
    uv run python 01-naive-rag/ingest.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chromadb

from common.llm import get_embeddings
from common.loaders import chunk_documents, load_markdown_docs

# Persist next to this stage so the reader can find the store next to the code.
CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "meridian_docs"


def ingest() -> None:
    docs = load_markdown_docs()
    chunks = chunk_documents(docs)
    print(f"Loaded {len(docs)} docs → {len(chunks)} chunks")

    # Rebuild from scratch so re-running ingest never leaves stale embeddings.
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # Embed via common/llm so API key / base URL / model stay in one place.
    embeddings = get_embeddings()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.create_collection(name=COLLECTION_NAME)

    ids = [f"chunk-{i}" for i in range(len(chunks))]
    texts = [c.page_content for c in chunks]
    metadatas = [{"source": c.metadata.get("source", "unknown")} for c in chunks]
    vectors = embeddings.embed_documents(texts)

    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=vectors,
    )
    print(f"Wrote collection '{COLLECTION_NAME}' → {CHROMA_DIR} ({len(ids)} vectors)")


if __name__ == "__main__":
    ingest()
