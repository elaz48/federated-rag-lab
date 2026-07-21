"""CLI for the stage-03 federated graph.

Run from the repo root (after seed + stage-01 ingest):
    uv run python 03-federated/ask.py \\
      "Which plan is Orbit Fintech on, and what does that plan include?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph import run_question  # noqa: E402  — local stage module


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Federated RAG: docs and/or sql with fusion"
    )
    parser.add_argument("question", help="Question to ask")
    args = parser.parse_args()

    result = run_question(args.question)

    print("=== Route ===")
    print(f"sources: {result.get('sources')}")
    print(f"reason: {result.get('route_reason')}")

    print("\n=== Snippets (pre-fusion bag) ===")
    for i, snip in enumerate(result.get("snippets") or [], start=1):
        print(
            f"\n--- snippet {i} | origin={snip.get('origin')} "
            f"| {snip.get('source')} ---"
        )
        print(snip.get("text", ""))

    print("\n=== Fused context ===")
    print(result.get("context", ""))

    print("\n=== Answer ===")
    print(result.get("answer", ""))


if __name__ == "__main__":
    main()
