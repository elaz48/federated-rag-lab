"""Naive RAG: retrieve top-k chunks from Chroma and stuff them into one prompt.

Run from the repo root (after ingest):
    uv run python 01-naive-rag/ask.py "What does the Professional plan include?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chromadb
from langchain_core.messages import HumanMessage, SystemMessage

from common.llm import get_chat_model, get_embeddings

CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "meridian_docs"
TOP_K = 4

SYSTEM_PROMPT = """You are a helpful assistant for Meridian Analytics.
Answer using ONLY the context chunks below. If the context does not contain
the answer, say you do not know — do not invent facts from outside the context.

Context:
{context}
"""


def get_collection() -> chromadb.Collection:
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"No Chroma store at {CHROMA_DIR}. Run: uv run python 01-naive-rag/ingest.py"
        )
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(name=COLLECTION_NAME)


def retrieve(question: str, k: int = TOP_K) -> list[dict[str, str]]:
    """Return the top-k chunks with source labels."""
    collection = get_collection()
    query_vec = get_embeddings().embed_query(question)
    result = collection.query(
        query_embeddings=[query_vec],
        n_results=k,
        include=["documents", "metadatas"],
    )
    documents = result["documents"][0] if result["documents"] else []
    metadatas = result["metadatas"][0] if result["metadatas"] else []

    chunks: list[dict[str, str]] = []
    for text, meta in zip(documents, metadatas, strict=True):
        chunks.append(
            {
                "source": str(meta.get("source", "unknown")),
                "text": text,
            }
        )
    return chunks


def format_context(chunks: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[chunk {i} | source={chunk['source']}]\n{chunk['text']}")
    return "\n\n".join(parts)


def answer_question(question: str, k: int = TOP_K) -> tuple[str, list[dict[str, str]]]:
    chunks = retrieve(question, k=k)
    context = format_context(chunks)
    llm = get_chat_model()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        HumanMessage(content=question),
    ]
    response = llm.invoke(messages)
    content = response.content
    # Chat models usually return str; coerce edge cases for printing.
    text = content if isinstance(content, str) else str(content)
    return text, chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Naive RAG over Meridian docs")
    parser.add_argument("question", help="Question to ask")
    parser.add_argument(
        "-k",
        type=int,
        default=TOP_K,
        help=f"Number of chunks to retrieve (default {TOP_K})",
    )
    args = parser.parse_args()

    answer, chunks = answer_question(args.question, k=args.k)

    print("=== Retrieved chunks ===")
    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- chunk {i} | {chunk['source']} ---")
        print(chunk["text"])
    print("\n=== Answer ===")
    print(answer)


if __name__ == "__main__":
    main()
