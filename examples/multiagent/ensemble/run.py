# -*- coding: utf-8 -*-
"""Runnable example — multi-agent ensemble (3 personas + coordinator).

Demonstrates the public API introduced by issues #150 / #151:

- :class:`atendentepro.ParallelNetwork` — fanout via ``asyncio.gather``
  with per-agent timeout + semaphore-bounded concurrency, then a
  coordinator merges the signals into the final string.
- :func:`atendentepro.signal_subclass` — generates the per-persona
  :class:`AgentSignal` subclass declared in ``client_resources/signals.py``.
- :class:`atendentepro.BaseNetwork` — Protocol that both
  :class:`AgentNetwork` and :class:`ParallelNetwork` satisfy.

The example is **mock-only** — no LLM calls are made. We monkeypatch
``atendentepro.multiagent.invoke._runner_run`` to feed canned per-agent
responses (the same trick used by ``tests/multiagent/conftest.py``). To
run against a real provider, delete the ``_patch_runner`` block, drop
``multiagent_config.yaml`` into ``client_templates/<your_client>/`` and
build the network with
``create_parallel_network(templates_root, client="<your_client>")``.

Run from the example directory::

    cd docs/examples/multiagent/ensemble
    PYTHONPATH=../../../.. python run.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Make ``client_resources`` (sibling package) importable when the script
# is run from this directory. Mirrors what production deployments get
# for free via PYTHONPATH / the ``client_templates`` folder layout.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from client_resources.signals import PersonaSignal  # noqa: E402

from atendentepro import (  # noqa: E402  (sys.path tweak above)
    AgentMetadata,
    BaseNetwork,
    ParallelNetwork,
)
from atendentepro.multiagent import invoke as invoke_mod  # noqa: E402

# ---------------------------------------------------------------------------
# 1. Stub agents — only ``name`` is consulted by ``invoke_agent``
# ---------------------------------------------------------------------------


class _StubAgent:
    """Stand-in for an SDK ``Agent``. ``ParallelNetwork`` only stores
    the instance and forwards it to ``invoke_agent``; the patched
    ``_runner_run`` (below) routes by ``agent.name`` so we don't need
    a real Runner / Model / OpenAI client."""

    def __init__(self, name: str) -> None:
        self.name = name


# ---------------------------------------------------------------------------
# 2. Mock the SDK Runner — feed canned per-agent outputs
# ---------------------------------------------------------------------------


class _FakeRunResult:
    """Mimics the SDK ``RunResult`` (only ``final_output`` is consulted)."""

    def __init__(self, final_output: Any) -> None:
        self.final_output = final_output


def _patch_runner(canned: Dict[str, Any]) -> None:
    """Replace ``_runner_run`` with a router keyed by ``agent.name``."""

    async def fake_runner_run(agent: Any, messages: list) -> _FakeRunResult:
        agent_name = getattr(agent, "name", "")
        if agent_name not in canned:
            raise AssertionError(f"unexpected agent invoked: {agent_name!r}")
        return _FakeRunResult(canned[agent_name])

    invoke_mod._runner_run = fake_runner_run  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 3. Demo
# ---------------------------------------------------------------------------


async def demo_parallel_network() -> None:
    """Build a ParallelNetwork, run it, and print the coordinator string."""
    print("--- Demo: ParallelNetwork (3 personas + coordinator) ---")

    # The dotted-path allowlist gates ``output_schema`` resolution at
    # build-time inside the production factory (``create_parallel_network``).
    # Here we hand the schema to ``AgentMetadata`` directly to keep the
    # example self-contained. Production usage stays declarative — see
    # ``multiagent_config.yaml`` next to this file.
    schema = "client_resources.signals.PersonaSignal"

    agents: Dict[str, _StubAgent] = {
        "persona_value": _StubAgent("persona_value"),
        "persona_growth": _StubAgent("persona_growth"),
        "persona_macro": _StubAgent("persona_macro"),
        "portfolio_manager": _StubAgent("portfolio_manager"),
    }
    metadata: Dict[str, AgentMetadata] = {
        "persona_value": AgentMetadata(exposed_to_user=False, output_schema=schema),
        "persona_growth": AgentMetadata(exposed_to_user=False, output_schema=schema),
        "persona_macro": AgentMetadata(exposed_to_user=False, output_schema=schema),
        "portfolio_manager": AgentMetadata(exposed_to_user=True),
    }

    # Canned outputs: each persona returns a typed PersonaSignal; the
    # coordinator returns the final user-facing string. The stub Runner
    # can already return parsed BaseModel instances (mirroring an SDK
    # ``Agent(output_type=PersonaSignal)`` configuration).
    canned: Dict[str, Any] = {
        "persona_value": PersonaSignal(
            agent_name="persona_value",
            verdict="approve",
            confidence=72,
            reasoning="Trading at 0.85x intrinsic value with stable cashflows.",
            recommendation="BUY",
            horizon_months=24,
        ),
        "persona_growth": PersonaSignal(
            agent_name="persona_growth",
            verdict="neutral",
            confidence=55,
            reasoning="TAM expansion plausible but execution risk remains.",
            recommendation="HOLD",
            horizon_months=12,
        ),
        "persona_macro": PersonaSignal(
            agent_name="persona_macro",
            verdict="approve",
            confidence=68,
            reasoning="Defensive sector benefits from the rate-cut cycle.",
            recommendation="BUY",
            horizon_months=18,
        ),
        # Coordinator output is a free-form string — exactly what
        # ``ParallelNetwork.run`` returns to the caller.
        "portfolio_manager": (
            "Portfolio Manager: 2/3 personas recommend BUY (value & macro), "
            "1/3 HOLD (growth). Net call: BUY with a 18-month horizon."
        ),
    }
    _patch_runner(canned)

    network: BaseNetwork = ParallelNetwork(
        agents=agents,  # type: ignore[arg-type]  # _StubAgent is duck-typed for invoke_agent
        fanout=["persona_value", "persona_growth", "persona_macro"],
        coordinator="portfolio_manager",
        agent_metadata=metadata,
        timeout_s=30.0,
        max_concurrency=10,
        partial_ok=False,
    )

    messages: List[Dict[str, Any]] = [{"role": "user", "content": "Stock pick para 12 meses"}]
    final = await network.run(messages)

    # Sanity check: the returned string MUST be the coordinator's text.
    # ParallelNetwork mints a fresh MultiAgentState internally per run
    # (it does not expose it on the network instance), so we assert on
    # the return value rather than on ``state.agent_calls``.
    assert "Portfolio Manager" in final
    assert "BUY" in final
    print(f"  fanout: {network.fanout}")
    print(f"  coordinator: {network.coordinator}")
    print(f"  final answer: {final}")


async def main() -> None:
    await demo_parallel_network()
    print("\nOK — multi-agent ensemble demo finished.")


if __name__ == "__main__":
    asyncio.run(main())
