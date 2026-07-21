"""Federated RAG: route to one or both sources, fan-out, fuse, generate.

    router → parallel (docs_retriever and/or sql_retriever) → fusion → generate
"""

from __future__ import annotations

import operator
import sys
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chromadb

from common.llm import get_chat_model, get_embeddings
from common.loaders import repo_root
from common.sql import router_source_catalog, run_select, schema_for_sql_writer

CHROMA_DIR = repo_root() / "01-naive-rag" / "chroma_db"
COLLECTION_NAME = "meridian_docs"
TOP_K = 4

SourceName = Literal["docs", "sql"]


class RouteDecision(BaseModel):
    """Router may select one or both sources (unlike stage 02)."""

    sources: list[SourceName] = Field(
        min_length=1,
        description="One or both of: docs (markdown), sql (customer rows)",
    )
    reason: str = Field(description="One short sentence explaining the selection")

    @field_validator("sources")
    @classmethod
    def dedupe_preserve_order(cls, v: list[SourceName]) -> list[SourceName]:
        return list(dict.fromkeys(v))


class SqlQuery(BaseModel):
    sql: str = Field(description="A single SQLite SELECT")


class GraphState(TypedDict, total=False):
    question: str
    sources: list[str]
    route_reason: str
    # Parallel retrievers append; fusion reads the combined list.
    snippets: Annotated[list[dict[str, str]], operator.add]
    context: str
    answer: str


def router_node(state: GraphState) -> dict[str, Any]:
    # Catalog includes live customer names + need-based rules (not topic-only).
    decision = get_chat_model().with_structured_output(RouteDecision).invoke(
        [
            SystemMessage(
                content=(
                    "You are the source router for Meridian Analytics federated RAG.\n"
                    "Select one or both of: docs, sql.\n\n"
                    f"{router_source_catalog()}"
                )
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    assert isinstance(decision, RouteDecision)
    return {"sources": decision.sources, "route_reason": decision.reason}


def fan_out(state: GraphState) -> list[Send]:
    """Map selected sources to parallel retriever invocations."""
    question = state["question"]
    sends: list[Send] = []
    for src in state.get("sources") or []:
        if src == "docs":
            sends.append(Send("docs_retriever", {"question": question}))
        elif src == "sql":
            sends.append(Send("sql_retriever", {"question": question}))
    if not sends:
        # Should not happen (schema min_length=1); fail closed to docs.
        sends.append(Send("docs_retriever", {"question": question}))
    return sends


def docs_retriever_node(state: GraphState) -> dict[str, Any]:
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"No Chroma at {CHROMA_DIR}. Run: uv run python 01-naive-rag/ingest.py"
        )
    collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_collection(
        COLLECTION_NAME
    )
    result = collection.query(
        query_embeddings=[get_embeddings().embed_query(state["question"])],
        n_results=TOP_K,
        include=["documents", "metadatas"],
    )
    docs = result["documents"][0] if result["documents"] else []
    metas = result["metadatas"][0] if result["metadatas"] else []
    snippets: list[dict[str, str]] = []
    for text, meta in zip(docs, metas, strict=True):
        snippets.append(
            {
                "origin": "docs",
                "source": str(meta.get("source", "unknown")),
                "text": text,
            }
        )
    return {"snippets": snippets}


def sql_retriever_node(state: GraphState) -> dict[str, Any]:
    drafted = get_chat_model().with_structured_output(SqlQuery).invoke(
        [
            SystemMessage(
                content=(
                    "Write one SQLite SELECT for the question.\n"
                    f"{schema_for_sql_writer()}"
                )
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    assert isinstance(drafted, SqlQuery)
    rows = run_select(drafted.sql)
    text = f"SQL:\n{drafted.sql.strip()}\n\nRows ({len(rows)}):\n{rows!r}"
    return {
        "snippets": [{"origin": "sql", "source": "structured.sqlite", "text": text}]
    }


def fusion_node(state: GraphState) -> dict[str, str]:
    """Merge multi-source snippets: label origin, drop exact duplicate texts.

    No reranking — keep the merge explainable for the teaching lab.
    """
    seen: set[str] = set()
    parts: list[str] = []
    for snip in state.get("snippets") or []:
        text = snip.get("text", "")
        key = text.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        origin = snip.get("origin", "?")
        source = snip.get("source", "")
        parts.append(f"[{origin} | {source}]\n{text}")
    return {"context": "\n\n".join(parts)}


def generate_node(state: GraphState) -> dict[str, str]:
    sources = ", ".join(state.get("sources") or [])
    response = get_chat_model().invoke(
        [
            SystemMessage(
                content=(
                    "Answer using ONLY the fused context. Each block is labeled with "
                    "its origin (docs or sql). If the context is insufficient, say "
                    "you do not know.\n"
                    "When sql shows a per-customer flag or plan and docs describe the "
                    "general policy, reconcile them: customer rows win for that "
                    "account; if a flag is on despite plan limits, explain it as a "
                    "pilot/override using the docs language.\n\n"
                    f"Selected sources: {sources}\n"
                    f"Context:\n{state.get('context', '')}"
                )
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    content = response.content
    return {"answer": content if isinstance(content, str) else str(content)}


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("router", router_node)
    g.add_node("docs_retriever", docs_retriever_node)
    g.add_node("sql_retriever", sql_retriever_node)
    g.add_node("fusion", fusion_node)
    g.add_node("generate", generate_node)

    g.add_edge(START, "router")
    # fan_out returns Send objects → parallel branches, then fan-in at fusion.
    g.add_conditional_edges("router", fan_out, ["docs_retriever", "sql_retriever"])
    g.add_edge("docs_retriever", "fusion")
    g.add_edge("sql_retriever", "fusion")
    g.add_edge("fusion", "generate")
    g.add_edge("generate", END)
    return g.compile()


def run_question(question: str) -> GraphState:
    return build_graph().invoke({"question": question})
