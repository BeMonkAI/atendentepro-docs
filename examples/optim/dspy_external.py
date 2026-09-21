"""Reference: populate the AtendentePro optim cache with DSPy.

THIS FILE IS NOT IMPORTED BY ATENDENTEPRO. It exists as documentation
for callers who want to use DSPy-based prompt optimization. The user
installs DSPy themselves (``pip install dspy-ai``) and runs a script
like this OFFLINE to produce optimized prompts. AtendentePro at runtime
only reads the cache — it never imports DSPy.

This deliberate split keeps AtendentePro's supply-chain surface minimal:
no dependency on ``dspy-ai`` / ``litellm`` / transitive packages whose
security posture we cannot vet for every release.

Requirements (install in YOUR environment, NOT AtendentePro's):

    pip install dspy-ai>=2.5 atendentepro

Usage::

    python optim_dspy_external.py \\
        --prompt-file canonical_prompts/triage.txt \\
        --model gpt-4.1-mini \\
        --provider openai \\
        --trainset trainset.jsonl \\
        --optimizer mipro_v2

Produces ``~/.atendentepro/optim_cache/<hash>/<model>.json`` that
AtendentePro picks up automatically at the next ``_build_agent`` call
when ``prompt_optim_mode`` is ``"fallback"`` or ``"force"``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

# User-installed; not a dependency of atendentepro.
import dspy  # type: ignore[import-not-found]

from atendentepro.optim import compose_lm_model_string, store_optimized_prompt


def build_lm(model: str, provider: str) -> Any:
    """Build a ``dspy.LM`` for the target (provider, model).

    Credentials (api_key, api_base) are read from the usual LiteLLM env
    vars (``OPENAI_API_KEY``, ``AZURE_API_KEY`` + ``AZURE_API_BASE``,
    etc.). Adapt this function to your provider's auth.
    """
    lm_spec = compose_lm_model_string(provider, model)
    return dspy.LM(lm_spec)


def build_signature(canonical_text: str) -> type:
    """Wrap a canonical prompt into a minimal ``dspy.Signature``.

    Input ``message`` / output ``response``. The canonical text becomes
    the signature docstring; MIPROv2 will refine it and the tuned
    docstring after compile is what we cache.
    """

    class PromptSignature(dspy.Signature):  # type: ignore[misc]
        """placeholder"""

        message: str = dspy.InputField(desc="User message to the agent.")
        response: str = dspy.OutputField(desc="Agent response.")

    PromptSignature.__doc__ = canonical_text
    return PromptSignature


def build_optimizer(
    name: str,
    metric: Callable[[Any, Any], bool],
) -> Any:
    if name == "mipro_v2":
        return dspy.MIPROv2(metric=metric, auto="light")
    if name == "bootstrap_fewshot":
        return dspy.BootstrapFewShot(metric=metric, max_bootstrapped_demos=4)
    raise ValueError(f"Unknown optimizer: {name!r}")


def extract_instructions(compiled: Any) -> str:
    predictors = list(compiled.predictors())
    if not predictors:
        raise RuntimeError("Compiled program has no predictors.")
    doc = (getattr(predictors[0].signature, "__doc__", None) or "").strip()
    if not doc:
        raise RuntimeError("Optimized signature docstring is empty.")
    return doc


def default_metric(example: Any, prediction: Any) -> bool:
    """Replace with your real evaluation (ValidationEngine / pass-rate /
    semantic match — whatever suits your use case).
    """
    return True


def load_trainset(path: Path) -> list[Any]:
    """Load a JSONL trainset into ``dspy.Example`` objects.

    Each line must have ``message`` + ``response`` keys.
    """
    examples: list[Any] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            examples.append(dspy.Example(**row).with_inputs("message"))
    return examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--trainset", required=True, type=Path)
    parser.add_argument(
        "--optimizer", default="mipro_v2", choices=("mipro_v2", "bootstrap_fewshot")
    )
    args = parser.parse_args()

    canonical_text = args.prompt_file.read_text(encoding="utf-8")
    trainset = load_trainset(args.trainset)

    lm = build_lm(args.model, args.provider)
    signature = build_signature(canonical_text)
    program = dspy.Predict(signature)
    optimizer = build_optimizer(args.optimizer, default_metric)

    started = time.monotonic()
    with dspy.context(lm=lm):
        compiled = optimizer.compile(program, trainset=trainset)
    elapsed = time.monotonic() - started

    optimized_text = extract_instructions(compiled)
    path = store_optimized_prompt(
        canonical_text,
        args.model,
        optimized_text,
        provider=args.provider,
        metadata={
            "optimizer": args.optimizer,
            "trainset_size": len(trainset),
            "compile_seconds": round(elapsed, 2),
            "timestamp": time.time(),
        },
    )
    print(f"Stored optimized prompt: {path}")


if __name__ == "__main__":
    sys.exit(main())
