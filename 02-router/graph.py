"""LangGraph router: pick exactly one source (docs | sql), retrieve, generate.

    router → (docs_retriever | sql_retriever) → generate
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chromadb

from common.llm import get_chat_model, get_embeddings
from common.loaders import repo_root
from common.sql import run_select, schema_for_sql_writer

CHROMA_DIR = repo_root() / "01-naive-rag" / "chroma_db"
COLLECTION_NAME = "meridian_docs"
TOP_K = 4


class RouteDecision(BaseModel):
    source: Literal["docs", "sql"] = Field(
        description="docs=product markdown; sql=customer/plan/flag rows"
    )
    reason: str = Field(description="One short sentence for the choice")


class SqlQuery(BaseModel):
    sql: str = Field(description="A single SQLite SELECT")


class GraphState(TypedDict, total=False):
    question: str
    source: str
    route_reason: str
    context: str
    snippets: list[dict[str, str]]
    answer: str


def router_node(state: GraphState) -> dict[str, str]:
    # Structured output beats free-text "use SQL" that the graph cannot branch on.
    decision = get_chat_model().with_structured_output(RouteDecision).invoke(
        [
            SystemMessage(
                content=(
                    "Route Meridian Analytics questions to exactly one source:\n"
                    "- docs: pricing, product, security, onboarding, releases, SLAs\n"
                    "- sql: a named customer's plan, MRR, signup, or feature flags\n"
                    "If both matter, pick the one source most needed (this stage "
                    "cannot use both)."
                )
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    assert isinstance(decision, RouteDecision)
    return {"source": decision.source, "route_reason": decision.reason}


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
    parts: list[str] = []
    for i, (text, meta) in enumerate(zip(docs, metas, strict=True), start=1):
        src = str(meta.get("source", "unknown"))
        snippets.append({"origin": "docs", "source": src, "text": text})
        parts.append(f"[docs {i} | {src}]\n{text}")
    return {"context": "\n\n".join(parts), "snippets": snippets}


def sql_retriever_node(state: GraphState) -> dict[str, Any]:
    # schema_for_sql_writer() includes live plan/flag literals (case-sensitive).
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
        "context": text,
        "snippets": [{"origin": "sql", "source": "structured.sqlite", "text": text}],
    }


def generate_node(state: GraphState) -> dict[str, str]:
    response = get_chat_model().invoke(
        [
            SystemMessage(
                content=(
                    "Answer using ONLY the context. If insufficient, say you do not "
                    "know.\n\n"
                    f"Routed source: {state.get('source', '?')}\n"
                    f"Context:\n{state.get('context', '')}"
                )
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    content = response.content
    return {"answer": content if isinstance(content, str) else str(content)}


def _pick_retriever(state: GraphState) -> Literal["docs_retriever", "sql_retriever"]:
    return "docs_retriever" if state.get("source") == "docs" else "sql_retriever"


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("router", router_node)
    g.add_node("docs_retriever", docs_retriever_node)
    g.add_node("sql_retriever", sql_retriever_node)
    g.add_node("generate", generate_node)
    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router",
        _pick_retriever,
        {"docs_retriever": "docs_retriever", "sql_retriever": "sql_retriever"},
    )
    g.add_edge("docs_retriever", "generate")
    g.add_edge("sql_retriever", "generate")
    g.add_edge("generate", END)
    return g.compile()


def run_question(question: str) -> GraphState:
    return build_graph().invoke({"question": question})
