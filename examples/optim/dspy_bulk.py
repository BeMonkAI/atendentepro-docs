"""Compile every AtendentePro canonical prompt for a target model.

Typical workflow when rolling out a new model to a client: you have a
trainset of representative conversations and you want to get optimized
variants of ALL 10 agents (triage, flow, interview, ...) in one pass,
so the runtime can hit the cache for every agent build.

Usage::

    pip install dspy-ai>=2.5
    export OPENAI_API_KEY=sk-...

    python optim_dspy_bulk.py \\
        --model gpt-4.1-mini \\
        --provider openai \\
        --trainset trainset.jsonl \\
        --agents triage,flow,interview,answer

``--agents all`` compiles every builder. Each run produces one cache
entry per (canonical_hash, model) pair — the same entries AtendentePro
reads at ``_build_agent`` time.

Requirements (YOUR environment, not AtendentePro's):
    pip install dspy-ai atendentepro
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable

import dspy  # type: ignore[import-not-found]

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


def _trivial_metric(example: Any, prediction: Any) -> bool:
    """Replace this with your real evaluation.

    For illustration this returns True unconditionally; a real setup
    uses ``ValidationEngine`` from monkai-tester (see
    ``optim_with_tester_metric.py``) or a domain-specific comparator.
    """
    return True


def _load_trainset(path: Path) -> list[Any]:
    examples: list[Any] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            examples.append(dspy.Example(**row).with_inputs("message"))
    return examples


def _make_signature(canonical_text: str) -> type:
    class PromptSignature(dspy.Signature):  # type: ignore[misc]
        """placeholder"""

        message: str = dspy.InputField()
        response: str = dspy.OutputField()

    PromptSignature.__doc__ = canonical_text
    return PromptSignature


def _extract_instructions(compiled: Any) -> str:
    predictors = list(compiled.predictors())
    doc = (getattr(predictors[0].signature, "__doc__", None) or "").strip()
    if not doc:
        raise RuntimeError("Compiled signature has empty docstring.")
    return doc


def _compile_one(
    canonical_text: str,
    model: str,
    provider: str,
    trainset: list[Any],
    metric: Callable[[Any, Any], bool],
) -> tuple[str, dict]:
    """Compile a single prompt. Returns (optimized_text, metadata)."""
    signature = _make_signature(canonical_text)
    program = dspy.Predict(signature)
    optimizer = dspy.MIPROv2(metric=metric, auto="light")

    lm = dspy.LM(compose_lm_model_string(provider, model))
    started = time.monotonic()
    with dspy.context(lm=lm):
        compiled = optimizer.compile(program, trainset=trainset)
    elapsed = time.monotonic() - started

    return _extract_instructions(compiled), {
        "optimizer": "mipro_v2",
        "trainset_size": len(trainset),
        "compile_seconds": round(elapsed, 2),
        "timestamp": time.time(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--trainset", type=Path, required=True)
    parser.add_argument(
        "--agents",
        default="all",
        help="Comma-separated list from triage/flow/... or 'all'.",
    )
    args = parser.parse_args()

    from atendentepro import prompts as atd_prompts

    agents: Iterable[str]
    if args.agents == "all":
        agents = sorted(_BUILDERS)
    else:
        agents = [a.strip() for a in args.agents.split(",") if a.strip()]
        for a in agents:
            if a not in _BUILDERS:
                raise SystemExit(f"Unknown agent {a!r}. Valid: {sorted(_BUILDERS)}")

    trainset = _load_trainset(args.trainset)
    print(f"Loaded {len(trainset)} examples. Compiling {len(list(agents))} agents.")

    for agent in agents:
        builder = getattr(atd_prompts, _BUILDERS[agent])
        canonical = builder()
        print(f"  [{agent}] compiling…", flush=True)
        optimized, metadata = _compile_one(
            canonical, args.model, args.provider, trainset, _trivial_metric
        )
        metadata["agent"] = agent
        path = store_optimized_prompt(
            canonical,
            args.model,
            optimized,
            provider=args.provider,
            metadata=metadata,
        )
        print(f"  [{agent}] stored {path} ({metadata['compile_seconds']}s)")


if __name__ == "__main__":
    sys.exit(main())
