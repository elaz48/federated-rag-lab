# Evaluation results

Same `dataset.jsonl` (10 questions: 4 docs / 3 sql / 3 both) run through
stages 01, 02, and 03. Metrics: RAGAS **faithfulness**, RAGAS
**context precision**, and LLM-judged **answer correctness** (0–1).

## Aggregate comparison

| Stage | Faithfulness | Context precision | Answer correctness |
|---|---:|---:|---:|
| `01-naive-rag` | 0.550 | 0.522 | 0.250 |
| `02-router` | 0.867 | 0.850 | 0.700 |
| `03-federated` | 0.860 | 0.839 | 0.800 |

## Answer correctness by question kind

| Stage | docs (n=4) | sql (n=3) | both (n=3) |
|---|---:|---:|---:|
| `01-naive-rag` | 0.625 | 0.000 | 0.000 |
| `02-router` | 0.625 | 1.000 | 0.500 |
| `03-federated` | 0.750 | 0.833 | 0.833 |

## Per-question answer correctness

| ID | Kind | `01-naive-rag` | `02-router` | `03-federated` | Question |
|---|---|---:|---:|---:|---|
| d1 | docs | 0.50 | 0.50 | 0.50 | What does the Professional plan include? |
| d2 | docs | 0.00 | 0.00 | 0.50 | Does Meridian support SAML SSO, and on which plan? |
| d3 | docs | 1.00 | 1.00 | 1.00 | How long is the Meridian free trial, and which features does it use? |
| d4 | docs | 1.00 | 1.00 | 1.00 | What is the target first-response time for a SEV-1 incident on the Enterprise plan? |
| s1 | sql | 0.00 | 1.00 | 1.00 | What plan is Acme Logistics on? |
| s2 | sql | 0.00 | 1.00 | 1.00 | What is the monthly recurring revenue (MRR) for Brightside Clinics? |
| s3 | sql | 0.00 | 1.00 | 0.50 | What plan is Orbit Fintech on, and is the sso feature flag enabled for them? |
| b1 | both | 0.00 | 0.50 | 0.50 | Which plan is customer Orbit Fintech on, and what does that plan include? |
| b2 | both | 0.00 | 0.00 | 1.00 | Is Orbit Fintech allowed to use SSO, and why? |
| b3 | both | 0.00 | 1.00 | 1.00 | Which plan is Northwind Trading on, and does that plan include REST API access? |

## Notes

- Stage 01 never sees SQLite: sql/both correctness should lag.
- Stage 02 can hit one source only: multi-source (`both`) items often lose.
- Stage 03 should lead on `both` by fusing docs + sql (e.g. Orbit SSO pilot).
