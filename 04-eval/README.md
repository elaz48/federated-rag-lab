# Stage 04 — Evaluation

## What this stage does

Runs a fixed golden set (`dataset.jsonl`, 10 hand-written Q/A pairs) through
**the same three pipelines** from earlier stages and scores them side by side:

| Kind | Count | Answer lives in… |
|---|---:|---|
| `docs` | 4 | Markdown only |
| `sql` | 3 | SQLite only |
| `both` | 3 | Needs customer rows **and** product/policy docs |

```bash
# prerequisites: .env, uv sync, seed, stage-01 ingest
uv run python scripts/seed_structured.py
uv run python 01-naive-rag/ingest.py
uv run python 04-eval/run_eval.py
```

`run_eval.py` writes `results.md` (also committed as a worked example).

## Metrics (one paragraph each)

**Faithfulness (RAGAS).** Does the generated answer stick to the retrieved
context, or does it invent facts? High faithfulness means claims in the answer
are supported by the context bags — it does *not* mean the answer is complete
or that the right source was retrieved.

**Context precision (RAGAS).** Of the chunks/rows returned, how much was
actually useful for answering the question (given the ground-truth reference)?
Low precision often means noisy retrieval or routing to the wrong store.

**Answer correctness (LLM judge).** Exact-ish graded score (0 / 0.5 / 1 averaged)
comparing the candidate answer to the hand-written ground truth. Wording may
differ; key facts must match. This is the metric that best shows stage 03
winning on multi-source items.

## How to read the table

1. Start with the **aggregate** table in `results.md` — overall means per stage.
2. Read **correctness by kind**. Stage 01 can look fine on `docs` and collapse on
   `sql`/`both`. Stage 02 should lift `sql` but still struggle on `both`. Stage 03
   should lead on `both`.
3. Use the **per-question** rows to debug: an id like `b2` (Orbit SSO pilot) is a
   canary for multi-source routing + fusion.

## Why stage 03 wins on multi-source questions

`both` items need a named customer's row **and** plan/policy text (e.g. Orbit
Fintech SSO pilot override). Stage 01 has no SQL. Stage 02 picks one source and
drops half the evidence. Stage 03 fans out to both, fuses labeled snippets, and
generates from the combined bag — so correctness on `both` should rise even when
aggregate faithfulness is similar (all stages can be "faithful" to incomplete
context).

## What I would add before production

- **Regression suite in CI** — fail the build if golden correctness drops below a floor.
- **Golden dataset ownership** — named maintainer, review process for new cases, no silent edits.
- **Drift monitoring** — track metric distributions over time as docs, schema, and models change.
- Empty-SQL repair loops, per-source timeouts, and human review on low-confidence answers.
