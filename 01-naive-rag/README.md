# Stage 01 — Naive RAG

## What this stage is

**Naive RAG** is the simplest useful pattern: embed documents once, retrieve the
nearest chunks for a question, stuff those chunks into a single prompt, and let
the LLM answer. There is no routing, no structured data, and no multi-step graph.

In this folder:

1. `ingest.py` loads `data/docs/*.md`, splits them (~500 chars, 50 overlap),
   embeds with `EMBEDDING_MODEL`, and persists vectors in `chroma_db/`.
2. `ask.py` embeds the question, pulls top-k (default 4) chunks, builds one
   prompt, and prints **both** the retrieved chunks and the model answer so you
   can see what the model actually saw.

Shared helpers live in `common/llm.py` and `common/loaders.py`.

## Failure modes (why later stages exist)

| Limitation | What breaks |
|---|---|
| **Single source** | Only markdown docs are indexed. Customer plans, MRR, and feature flags live in SQLite and are invisible here. |
| **No routing** | Every question hits the vector store, even when the answer is a SQL fact. |
| **Stuffing only** | One prompt, one shot. No fan-out, no fusion, no second retrieval pass. |
| **Retriever quality** | If the right chunk is not in top-k, the model cannot answer — even if the doc set contains it. |

## Run

From the repo root, with `.env` configured and dependencies installed:

```bash
uv sync
uv run python 01-naive-rag/ingest.py
uv run python 01-naive-rag/ask.py "What does the Professional plan include?"
```

## Example run

A real capture lives in [`example-output.md`](example-output.md). Summary:

**1. Docs question** — *What does the Professional plan include?*

> The Professional plan includes REST API access, advanced export, and more seats and monitors.

Correct but thin: the model only used the scattered prose that landed in top-k. The full pricing comparison table never made it into the retrieved chunks, so seats, monitor limits, and other plan cells never reached the prompt.

**2. Structured question** — *What plan is Orbit Fintech on, and is SSO enabled for them?*

> I do not know.

Retrieval was strong (SSO, plan matrix, pilot flag language), yet the model correctly refused: Orbit Fintech’s plan and `sso` flag live in SQLite, not the doc corpus. Naive RAG has no SQL path — Stage 02 adds one.

## Try this

1. **Docs-only (should work):**  
   `uv run python 01-naive-rag/ask.py "What does the Professional plan include?"`  
   Expect pricing FAQ content (API, advanced export, seats, etc.).

2. **Docs-only (security):**  
   `uv run python 01-naive-rag/ask.py "Does Meridian support SAML SSO, and on which plan?"`  
   Expect Enterprise-gated SSO from the security / pricing docs.

3. **Structured-only (should fail or refuse):**  
   `uv run python 01-naive-rag/ask.py "What plan is Orbit Fintech on, and is SSO enabled for them?"`  
   The answer lives in SQLite (`customers` + `feature_flags`), not in the docs.
   Naive RAG has no path to that data — the model should say it does not know
   (or guess wrongly from general plan text). Stage 02 introduces a SQL path;
   Stage 03 can combine both sources.
