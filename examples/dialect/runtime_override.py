"""Force a specific dialect for a single chat call, at runtime.

Typical use: you want to A/B test how the **same model** behaves with
two different dialect framings (e.g. Claude receives the canonical
prompt in XML-wrapped vs. passthrough form). The CLI exposes this via
``atendentepro test --dialect``; this script does the same thing from
Python so you can drive it from a notebook or custom harness.

Usage::

    OPENAI_API_KEY=sk-... \\
        python dialect_runtime_override.py \\
            --client my_client \\
            --message "oi, quero saber do produto X" \\
            --dialect claude

Output is the agent's response plus trace. Repeat with
``--dialect gpt`` (or unset) to compare.

Note: AtendentePro bakes the dialect into the agent instructions AT
BUILD TIME. This script rebuilds the network for each invocation —
that's cheap but not zero. For heavy benchmarking use
``monkai-tester --dialect both`` instead.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional

from atendentepro import configure, create_standard_network


async def run_once(client: str, message: str, templates_root: Path) -> dict:
    from agents import Runner

    network = create_standard_network(templates_root=templates_root, client=client)
    result = await Runner.run(network.triage, input=message)

    trace: list[str] = []
    for item in getattr(result, "raw_responses", []):
        name = getattr(item, "agent_name", None)
        if name and (not trace or trace[-1] != name):
            trace.append(name)

    final = getattr(result, "last_agent", None)
    final_name = getattr(final, "name", "unknown") if final else "unknown"
    return {
        "response": result.final_output or "",
        "agent": final_name,
        "trace": trace or [final_name],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument(
        "--dialect",
        default=None,
        choices=("gpt", "claude", "gemini", "grok", "llama"),
        help="Pin dialect for this run. Omit to let the registry resolve from (provider, model).",
    )
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument(
        "--templates-root", type=Path, default=Path("./client_templates")
    )
    args = parser.parse_args()

    configure_kwargs: dict[str, Any] = {
        "provider": args.provider,
        "default_model": args.model,
    }
    if args.dialect:
        configure_kwargs["prompt_dialect"] = args.dialect
    configure(**configure_kwargs)

    result = asyncio.run(run_once(args.client, args.message, args.templates_root))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
