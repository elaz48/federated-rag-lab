"""CLI for the stage-02 router graph.

Run from the repo root (after seed + stage-01 ingest):
    uv run python 02-router/ask.py "What plan is Orbit Fintech on?"
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
        description="Routed RAG: docs OR sql (exactly one source)"
    )
    parser.add_argument("question", help="Question to ask")
    args = parser.parse_args()

    result = run_question(args.question)

    print("=== Route ===")
    print(f"source: {result.get('source')}")
    print(f"reason: {result.get('route_reason')}")

    print("\n=== Retrieved context ===")
    for i, snip in enumerate(result.get("snippets") or [], start=1):
        label = snip.get("source") or snip.get("origin")
        print(f"\n--- snippet {i} | {label} ---")
        print(snip.get("text", ""))

    print("\n=== Answer ===")
    print(result.get("answer", ""))


if __name__ == "__main__":
    main()
