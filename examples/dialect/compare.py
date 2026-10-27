"""Render one agent's canonical prompt in every dialect for side-by-side inspection.

Usage::

    python dialect_compare.py --agent triage --output ./dialect_debug/

For each dialect (gpt, claude, gemini, grok, llama) writes a file
``<agent>.<dialect>.txt`` under the output directory, plus a single
``byte_counts.json`` summary. Useful when tuning dialect transforms
or diffing with a tool like ``diff -u`` / ``meld``.

The same functionality is exposed via the CLI:

    atendentepro dialect preview <agent> --output ./dialect_debug/

This script exists for callers who want to script the diff as part of
a larger pipeline (e.g. CI asserts that dialect output doesn't change
unexpectedly).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from atendentepro.prompts.dialect import apply_dialect
from atendentepro.prompts.dialect.transforms import KNOWN_DIALECTS

_BUILDERS = {
    "triage": "get_triage_prompt",
    "flow": "get_flow_prompt",
    "interview": "get_interview_prompt",
    "answer": "get_answer_prompt",
    "knowledge": "get_knowledge_prompt",
    "confirmation": "get_confirmation_prompt",
    "usage": "get_usage_prompt",
    "onboarding": "get_onboarding_prompt",
    "escalation": "get_escalation_prompt",
    "feedback": "get_feedback_prompt",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent", required=True, choices=sorted(_BUILDERS), help="Agent to render."
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Directory for rendered files."
    )
    args = parser.parse_args()

    from atendentepro import prompts as atd_prompts

    builder = getattr(atd_prompts, _BUILDERS[args.agent])
    canonical = builder()

    args.output.mkdir(parents=True, exist_ok=True)
    summary: dict = {}
    for dialect in sorted(KNOWN_DIALECTS):
        rendered = apply_dialect(canonical, dialect)
        path = args.output / f"{args.agent}.{dialect}.txt"
        path.write_text(rendered, encoding="utf-8")
        summary[dialect] = {"bytes": len(rendered), "path": str(path)}

    summary_path = args.output / "byte_counts.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {len(summary)} files + summary to {args.output}")


if __name__ == "__main__":
    sys.exit(main())
