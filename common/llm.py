"""OpenAI-compatible chat and embedding clients from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Load .env from the process cwd (repo root when scripts are run as documented).
load_dotenv()


def _require_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return key


def _base_url() -> str | None:
    # Empty string would break the client; treat blank as unset.
    value = os.getenv("OPENAI_BASE_URL")
    return value if value else None


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    """Chat model for generation, routing, SQL writing, and eval judging."""
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        api_key=_require_api_key(),
        base_url=_base_url(),
        temperature=0,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """Embedding model for indexing and retrieval."""
    return OpenAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=_require_api_key(),
        base_url=_base_url(),
    )
