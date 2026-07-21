"""Run the golden dataset against stages 01, 02, and 03; write results.md.

Usage (repo root, after seed + stage-01 ingest + .env):
    uv run python 04-eval/run_eval.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any, Callable

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.llm import get_chat_model, get_embeddings  # noqa: E402

DATASET_PATH = Path(__file__).resolve().parent / "dataset.jsonl"
RESULTS_PATH = Path(__file__).resolve().parent / "results.md"


# --- ragas import shim -------------------------------------------------------
# ragas 0.4.x imports ChatVertexAI from langchain_community; that module was
# removed. Stub it so evaluate() still loads (we only use OpenAI-compatible LLMs).
def _patch_ragas_imports() -> None:
    name = "langchain_community.chat_models.vertexai"
    if name not in sys.modules:
        mod = types.ModuleType(name)

        class ChatVertexAI:  # noqa: N801 — match upstream name
            pass

        mod.ChatVertexAI = ChatVertexAI
        sys.modules[name] = mod
    import langchain_community.llms as community_llms

    if not hasattr(community_llms, "VertexAI"):
        community_llms.VertexAI = type("VertexAI", (), {})


_patch_ragas_imports()

from datasets import Dataset  # noqa: E402
from ragas import evaluate  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.metrics import context_precision, faithfulness  # noqa: E402


class CorrectnessJudgment(BaseModel):
    """Exact-ish graded correctness: 1 = solid match, 0.5 = partial, 0 = wrong."""

    score: float = Field(ge=0.0, le=1.0)
    reason: str


Pipeline = Callable[[str], tuple[str, list[str]]]


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_pipelines() -> dict[str, Pipeline]:
    stage01 = _load_module(ROOT / "01-naive-rag" / "ask.py", "stage01_ask")
    stage02 = _load_module(ROOT / "02-router" / "graph.py", "stage02_graph")
    stage03 = _load_module(ROOT / "03-federated" / "graph.py", "stage03_graph")

    def run_01(question: str) -> tuple[str, list[str]]:
        answer, chunks = stage01.answer_question(question)
        return answer, [c["text"] for c in chunks]

    def run_02(question: str) -> tuple[str, list[str]]:
        result = stage02.run_question(question)
        snippets = result.get("snippets") or []
        contexts = [s["text"] for s in snippets] or [result.get("context") or ""]
        return result.get("answer") or "", contexts

    def run_03(question: str) -> tuple[str, list[str]]:
        result = stage03.run_question(question)
        snippets = result.get("snippets") or []
        contexts = [s["text"] for s in snippets] or [result.get("context") or ""]
        return result.get("answer") or "", contexts

    return {
        "01-naive-rag": run_01,
        "02-router": run_02,
        "03-federated": run_03,
    }


def load_dataset(path: Path = DATASET_PATH) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def judge_correctness(question: str, ground_truth: str, answer: str) -> float:
    judgment = get_chat_model().with_structured_output(CorrectnessJudgment).invoke(
        [
            SystemMessage(
                content=(
                    "Score whether the candidate answer matches the ground truth "
                    "for a Meridian Analytics lab question. "
                    "1.0 = key facts present and correct; "
                    "0.5 = partial credit (some key facts, or minor errors); "
                    "0.0 = wrong, empty, or refuses when the truth is answerable. "
                    "Ignore wording differences."
                )
            ),
            HumanMessage(
                content=(
                    f"Question: {question}\n"
                    f"Ground truth: {ground_truth}\n"
                    f"Candidate answer: {answer}"
                )
            ),
        ]
    )
    assert isinstance(judgment, CorrectnessJudgment)
    return float(judgment.score)


def run_pipeline_on_dataset(
    name: str, pipeline: Pipeline, rows: list[dict[str, str]]
) -> dict[str, Any]:
    answers: list[str] = []
    contexts_list: list[list[str]] = []
    correctness_scores: list[float] = []

    print(f"\n=== Pipeline {name} ===")
    for row in rows:
        q = row["question"]
        print(f"  [{row['id']}/{row['kind']}] {q[:72]}...")
        answer, contexts = pipeline(q)
        answers.append(answer)
        contexts_list.append(contexts)
        score = judge_correctness(q, row["ground_truth"], answer)
        correctness_scores.append(score)
        print(f"    correctness={score:.2f}")

    ds = Dataset.from_dict(
        {
            "user_input": [r["question"] for r in rows],
            "response": answers,
            "retrieved_contexts": contexts_list,
            "reference": [r["ground_truth"] for r in rows],
        }
    )
    ragas_llm = LangchainLLMWrapper(get_chat_model())
    ragas_emb = LangchainEmbeddingsWrapper(get_embeddings())
    result = evaluate(
        ds,
        metrics=[faithfulness, context_precision],
        llm=ragas_llm,
        embeddings=ragas_emb,
        show_progress=True,
    )
    # EvaluationResult supports dict-like / pandas export depending on version.
    table = result.to_pandas()
    faith_mean = float(table["faithfulness"].mean())
    # column name is the metric name
    cp_col = "context_precision" if "context_precision" in table.columns else table.columns[-1]
    # find context precision column robustly
    for col in table.columns:
        if "context_precision" in col or col == "context_precision":
            cp_col = col
            break
    cp_mean = float(table[cp_col].mean())
    corr_mean = sum(correctness_scores) / len(correctness_scores)

    # Per-kind correctness for the write-up
    by_kind: dict[str, list[float]] = {"docs": [], "sql": [], "both": []}
    for row, score in zip(rows, correctness_scores, strict=True):
        by_kind[row["kind"]].append(score)
    kind_means = {
        k: (sum(v) / len(v) if v else 0.0) for k, v in by_kind.items()
    }

    return {
        "faithfulness": faith_mean,
        "context_precision": cp_mean,
        "answer_correctness": corr_mean,
        "correctness_by_kind": kind_means,
        "per_row_correctness": correctness_scores,
    }


def write_results(
    rows: list[dict[str, str]],
    metrics: dict[str, dict[str, Any]],
    path: Path = RESULTS_PATH,
) -> None:
    stages = list(metrics.keys())
    lines: list[str] = [
        "# Evaluation results",
        "",
        "Same `dataset.jsonl` (10 questions: 4 docs / 3 sql / 3 both) run through",
        "stages 01, 02, and 03. Metrics: RAGAS **faithfulness**, RAGAS",
        "**context precision**, and LLM-judged **answer correctness** (0–1).",
        "",
        "## Aggregate comparison",
        "",
        "| Stage | Faithfulness | Context precision | Answer correctness |",
        "|---|---:|---:|---:|",
    ]
    for stage in stages:
        m = metrics[stage]
        lines.append(
            f"| `{stage}` | {m['faithfulness']:.3f} | "
            f"{m['context_precision']:.3f} | {m['answer_correctness']:.3f} |"
        )

    lines += [
        "",
        "## Answer correctness by question kind",
        "",
        "| Stage | docs (n=4) | sql (n=3) | both (n=3) |",
        "|---|---:|---:|---:|",
    ]
    for stage in stages:
        k = metrics[stage]["correctness_by_kind"]
        lines.append(
            f"| `{stage}` | {k['docs']:.3f} | {k['sql']:.3f} | {k['both']:.3f} |"
        )

    lines += [
        "",
        "## Per-question answer correctness",
        "",
        "| ID | Kind | " + " | ".join(f"`{s}`" for s in stages) + " | Question |",
        "|---|---|" + "|".join(["---:"] * len(stages)) + "|---|",
    ]
    for i, row in enumerate(rows):
        scores = " | ".join(
            f"{metrics[s]['per_row_correctness'][i]:.2f}" for s in stages
        )
        q_short = row["question"].replace("|", "/")
        lines.append(f"| {row['id']} | {row['kind']} | {scores} | {q_short} |")

    lines += [
        "",
        "## Notes",
        "",
        "- Stage 01 never sees SQLite: sql/both correctness should lag.",
        "- Stage 02 can hit one source only: multi-source (`both`) items often lose.",
        "- Stage 03 should lead on `both` by fusing docs + sql (e.g. Orbit SSO pilot).",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path}")


def main() -> None:
    rows = load_dataset()
    pipelines = load_pipelines()
    metrics: dict[str, dict[str, Any]] = {}
    for name, pipeline in pipelines.items():
        metrics[name] = run_pipeline_on_dataset(name, pipeline, rows)
    write_results(rows, metrics)


if __name__ == "__main__":
    main()
