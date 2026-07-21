# Stage 02 — Router (single source)

## What this stage adds

Stage 01 always hit the vector store. That fails for questions whose answer lives
only in SQLite (customer plan, MRR, feature flags).

This stage introduces **LangGraph** and a **router** that chooses **exactly one**
knowledge source before retrieval:

```
router → (docs_retriever | sql_retriever) → generate
```

| Node | Role |
|---|---|
| `router` | Structured output (`docs` or `sql`) plus a short reason |
| `docs_retriever` | Same Chroma collection as stage 01 (run ingest there first) |
| `sql_retriever` | LLM drafts a `SELECT`, guard rejects non-reads, rows become context |
| `generate` | Answer from the single context bag only |

Code: `graph.py` (graph + nodes), `ask.py` (CLI that prints route, context, answer).

## Why routing

Not every question wants the same tool. Routing keeps the pipeline simple while
sending customer-record questions to SQL and product/policy questions to docs.
Without it, you either over-fetch (waste + noise) or under-fetch (stage 01's
"I do not know" on Orbit Fintech).

## Why structured output for the route

Free-text "I'll use SQL" is brittle to parse and easy for the model to half-follow.
A Pydantic schema (`RouteDecision`) forces a closed enum (`docs` | `sql`) the
graph can branch on with `add_conditional_edges`. The `reason` field is for you:
inspect it when a route looks wrong.

## Limitation: one source per question

The router **cannot** select both. Multi-hop questions that need SQL *and* docs
fail partially — e.g. plan membership from the DB plus "what does that plan
include?" from the pricing FAQ. Stage 03 lifts this with fan-out and fusion.

## SQL safety (teaching-grade)

`sql_retriever` only accepts a single statement starting with `SELECT`, rejects
common write/DDL keywords, and opens SQLite with `mode=ro`. This is a lab guard,
not a production SQL firewall.

## Lesson: text-to-SQL needs value vocabulary, not just schemas

Table/column shapes are not enough. A real miss here: the model wrote
`flag = 'SSO'` while the database stores lowercase `'sso'`, so the query returned
**0 rows** and generation correctly fell back to "I do not know" — even though
routing to SQL was right.

The SQL-writer prompt therefore includes **live distinct values** for
`customers.plan` and `feature_flags.flag` (see `common/sql.schema_for_sql_writer`),
queried from the DB at runtime. Production systems go further (embeddings over
categorical values, constrained decoding, self-correction on empty results).

## Run

Prerequisites: `.env`, `uv sync`, seed, and stage-01 ingest (shared Chroma path).

```bash
uv run python scripts/seed_structured.py
uv run python 01-naive-rag/ingest.py
uv run python 02-router/ask.py "What plan is Orbit Fintech on?"
```

## Try this

1. **SQL path:**  
   `uv run python 02-router/ask.py "What plan is Orbit Fintech on, and is SSO enabled for them?"`  
   Expect route=`sql`, rows from `customers` + `feature_flags` (Professional, sso=1 pilot).

2. **Docs path:**  
   `uv run python 02-router/ask.py "What does the Professional plan include?"`  
   Expect route=`docs` and a pricing-oriented answer.

3. **Needs both (should fail or be incomplete):**  
   `uv run python 02-router/ask.py "Which plan is customer Orbit Fintech on, and what does that plan include?"`  
   The router picks one source. SQL can name the plan; docs can describe features;
   this stage cannot merge them. Stage 03 is built for that case.
