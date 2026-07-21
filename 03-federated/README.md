# Stage 03 — Federated (multi-source)

## What "federated" adds

Stage 02 routed to **exactly one** source. That breaks questions that need a
customer row *and* product documentation — for example:

> Which plan is Orbit Fintech on, and what does that plan include?

SQL knows the plan name; docs know the plan matrix. Federated RAG **selects one
or both** sources, retrieves in parallel, **fuses** the evidence, then generates.

```
router → parallel fan-out (docs and/or sql) → fusion → generate
```

| Node | Role |
|---|---|
| `router` | Structured output: `sources: ["docs"]`, `["sql"]`, or both |
| `docs_retriever` / `sql_retriever` | Same retrieval ideas as stage 02; run via LangGraph `Send` |
| `fusion` | Label each snippet with origin, simple exact-text dedup, build one context |
| `generate` | Answer from the fused, labeled context only |

Code: `graph.py`, `ask.py`. SQL vocabulary and the router source catalog come
from `common/sql.py` (live customer names, flag/plan literals).

## Lesson: route by data needs, not topic

A topic-only prompt ("SSO → security docs") can skip SQL even when a **named
customer** is in the question. Real miss: *"Is Orbit Fintech allowed to use SSO,
and why?"* routed to `['docs']` only → no flag row → "I do not know".

The router prompt now includes a **source inventory** (sql holds these customer
names; docs hold rules/policies) and explicit rules: named customer → sql
required; rules/plan contents → docs required; many questions need both.

## Fan-out / fan-in in LangGraph

After routing, `fan_out` returns a list of `Send(...)` objects — one per selected
source. LangGraph runs those nodes (conceptually in parallel) and **fans in** when
every branch has finished: both retrievers edge into `fusion`.

Retriever outputs append to `snippets` via an `Annotated[..., operator.add]`
reducer so parallel writes merge instead of overwriting.

## How fusion works here

Fusion is deliberately boring:

1. Keep snippet order as received.
2. Drop empty or exact-duplicate texts (normalized with `strip().lower()`).
3. Prefix each block with `[docs | filename]` or `[sql | structured.sqlite]`.

No score fusion, no cross-encoder rerank, no token budget packing. You should be
able to read the fused context and see exactly what the generator saw.

## What production systems add (not implemented)

- **Reranking** across sources after fusion
- **Per-source timeouts** and **partial failure** (answer from whatever returned)
- Source-specific auth, caching, and query budgets
- Empty-result repair loops for text-to-SQL
- Citation UX tied back to origin labels

## Run

```bash
uv run python scripts/seed_structured.py
uv run python 01-naive-rag/ingest.py
uv run python 03-federated/ask.py \
  "Which plan is Orbit Fintech on, and what does that plan include?"
```

## Try this

1. **Both sources:**  
   `uv run python 03-federated/ask.py "Which plan is Orbit Fintech on, and what does that plan include?"`  
   Expect `sources` to include both; answer names Professional and lists plan features.

2. **SQL-only still works:**  
   `uv run python 03-federated/ask.py "What plan is Orbit Fintech on, and is SSO enabled for them?"`  
   Expect sql (possibly docs too); Professional + sso enabled (pilot flag).

3. **Docs-only still works:**  
   `uv run python 03-federated/ask.py "What does the Professional plan include?"`  
   Expect docs route and a pricing-oriented answer.
