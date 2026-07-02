"""DSPy optimize with monkai-tester's ValidationEngine as the metric.

The trivial ``lambda example, prediction: True`` metric in the other
examples exists to show the wiring. For real work you want the
optimizer to actually score candidate prompts against something that
correlates with user-perceived quality.

monkai-tester already ships a ``ValidationEngine`` that compares an
agent's response against expected answer/sender/tool_calls fields from
a CSV fixture. Reusing it here means:

- Same definition of "pass" used in production benchmarks.
- Trainset comes from the client's existing Desempenho_*.csv files.
- No new evaluation harness to maintain.

Requirements (YOUR environment):
    pip install dspy-ai monkai-tester atendentepro

Usage::

    export OPENAI_API_KEY=sk-...
    export AZURE_OPENAI_KEY=...   # ValidationEngine runs GPT match agents
    export AZURE_OPENAI_ENDPOINT=...

    python optim_with_tester_metric.py \\
        --csv data/your_client/Desempenho_agentes_local.csv \\
        --agent answer \\
        --model gpt-4.1-mini \\
        --provider openai
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import dspy  # type: ignore[import-not-found]
from monkai_tester.utils import load_input_file  # type: ignore[import-not-found]
from monkai_tester.validation_engine import ValidationEngine  # type: ignore[import-not-found]

from atendentepro.optim import compose_lm_model_string, store_optimized_prompt

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


def rows_to_examples(rows: list, agent: str) -> list[Any]:
    """Convert monkai-tester CSV rows to dspy.Examples.

    Each row already has ``user_message`` and the expected response
    fields the ValidationEngine compares against. Only rows targeting
    the given ``agent`` are kept so the trainset matches the prompt
    we're tuning.
    """
    examples: list[Any] = []
    for row in rows:
        if getattr(row, "agent_to", None) != agent and getattr(row, "agent_from", None) != agent:
            continue
        examples.append(
            dspy.Example(
                message=row.user_message,
                response=row.expected_response or "",
                expected_parameters=row.parameters,
                expected_tool_calls=row.tool_calls,
                expected_sender=row.agent_to or row.agent_from,
            ).with_inputs("message")
        )
    return examples


def tester_metric(validator: ValidationEngine):
    """Return a DSPy-compatible metric that scores via ValidationEngine."""

    def _metric(example: Any, prediction: Any) -> bool:
        # prediction.response is what the tuned program emits.
        # ValidationEngine scores its 4 layers (parameters, tool_calls,
        # sender, content) and returns an overall_pass bool.
        result = validator.validate_test_case(
            expected_parameters=getattr(example, "expected_parameters", ""),
            actual_parameters="",
            expected_tool_calls=getattr(example, "expected_tool_calls", ""),
            actual_tool_calls="",
            expected_sender=getattr(example, "expected_sender", ""),
            actual_sender="",
            expected_answer=example.response,
            actual_answer=prediction.response,
        )
        return bool(result.overall_pass)

    return _metric


def _make_signature(canonical_text: str) -> type:
    class S(dspy.Signature):  # type: ignore[misc]
        """placeholder"""

        message: str = dspy.InputField()
        response: str = dspy.OutputField()

    S.__doc__ = canonical_text
    return S


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="monkai-tester CSV fixture.")
    parser.add_argument("--agent", required=True, choices=sorted(_BUILDERS))
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", default="openai")
    parser.add_argument(
        "--optimizer", default="mipro_v2", choices=("mipro_v2", "bootstrap_fewshot")
    )
    args = parser.parse_args()

    from atendentepro import prompts as atd_prompts

    builder = getattr(atd_prompts, _BUILDERS[args.agent])
    canonical = builder()

    rows = load_input_file(args.csv)
    trainset = rows_to_examples(rows, args.agent)
    if not trainset:
        raise SystemExit(
            f"CSV {args.csv} has no rows targeting agent {args.agent!r}."
        )
    print(f"Loaded {len(trainset)} examples for {args.agent}.")

    validator = ValidationEngine()
    metric = tester_metric(validator)

    signature = _make_signature(canonical)
    program = dspy.Predict(signature)

    if args.optimizer == "mipro_v2":
        optimizer = dspy.MIPROv2(metric=metric, auto="light")
    else:
        optimizer = dspy.BootstrapFewShot(metric=metric, max_bootstrapped_demos=4)

    lm = dspy.LM(compose_lm_model_string(args.provider, args.model))
    started = time.monotonic()
    with dspy.context(lm=lm):
        compiled = optimizer.compile(program, trainset=trainset)
    elapsed = time.monotonic() - started

    predictors = list(compiled.predictors())
    optimized_text = (predictors[0].signature.__doc__ or "").strip()
    if not optimized_text:
        raise RuntimeError("Compiled signature has empty docstring.")

    path = store_optimized_prompt(
        canonical,
        args.model,
        optimized_text,
        provider=args.provider,
        metadata={
            "optimizer": args.optimizer,
            "metric": "monkai_tester.ValidationEngine",
            "agent": args.agent,
            "trainset_size": len(trainset),
            "compile_seconds": round(elapsed, 2),
            "csv_source": str(args.csv),
            "timestamp": time.time(),
        },
    )
    print(f"Stored: {path}")


if __name__ == "__main__":
    sys.exit(main())
