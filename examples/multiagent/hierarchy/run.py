# -*- coding: utf-8 -*-
"""Runnable example — multi-agent hierarchy (manager + 2 specialists).

Demonstrates the public API introduced by issues #147 / #148 / #149:

- :class:`atendentepro.AgentMetadata` side-car (``exposed_to_user``,
  ``can_call``, ``output_schema``, ``builtin_tools``).
- :class:`atendentepro.MultiAgentState` for nested-call audit trail.
- :func:`atendentepro.invoke_agent` for a one-shot, schema-validated
  call to a specialist.
- :func:`atendentepro.build_call_agent_tool` for the per-caller-bound
  ``call_agent`` tool the manager would attach to its ``tools`` list.

The example is **mock-only** — no LLM calls are made. We monkeypatch
``atendentepro.multiagent.invoke._runner_run`` to feed canned JSON
responses, the same trick used by ``tests/multiagent/conftest.py``. To
run against a real provider, delete the ``patch_runner`` block, attach
this YAML to your ``client_templates/<client>/multiagent_config.yaml``,
and use ``create_standard_network``.

Run from the repo root::

    python -m docs.examples.multiagent.hierarchy.run
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

from atendentepro import (
    AgentMetadata,
    CallAgentForbidden,
    MultiAgentState,
    build_call_agent_tool,
    invoke_agent,
)
from atendentepro.multiagent import invoke as invoke_mod

# ---------------------------------------------------------------------------
# 1. Specialist signal schemas (would normally live in client_resources/)
# ---------------------------------------------------------------------------
#
# The example bypasses the dotted-path allowlist by setting
# ``output_schema=None`` on AgentMetadata and resolving the class
# manually inside the stub Runner — keeps the example self-contained.
# Production usage declares ``output_schema: client_resources.signals.X``
# in multiagent_config.yaml and lets ``invoke_agent`` resolve it.


class ValuationSignal(BaseModel):
    verdict: Literal["approve", "reject", "neutral"]
    fair_price: float
    reasoning: str


class RiskSignal(BaseModel):
    verdict: Literal["approve", "reject", "escalate"]
    risk_score: int = Field(ge=0, le=100)
    reasoning: str


# ---------------------------------------------------------------------------
# 2. Stub agents and a minimal AgentNetwork-like object
# ---------------------------------------------------------------------------


class _StubAgent:
    """Stand-in for an SDK ``Agent`` — only ``name`` is needed for invoke."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: List[Any] = []


class _StubNetwork:
    """Stand-in for ``AgentNetwork`` exposing the bare minimum the
    multiagent helpers need: ``agent_metadata`` dict and direct
    attribute access (``network.<name>``) per ``_resolve_target_agent``.
    """

    def __init__(self) -> None:
        self.manager = _StubAgent("manager")
        self.valuation_specialist = _StubAgent("valuation_specialist")
        self.risk_specialist = _StubAgent("risk_specialist")
        self.agent_metadata: Dict[str, AgentMetadata] = {
            "manager": AgentMetadata(
                exposed_to_user=True,
                can_call=["valuation_specialist", "risk_specialist"],
                builtin_tools=["call_agent"],
            ),
            "valuation_specialist": AgentMetadata(exposed_to_user=False),
            "risk_specialist": AgentMetadata(exposed_to_user=False),
        }

    def get_all_agents(self) -> List[_StubAgent]:
        return [self.manager, self.valuation_specialist, self.risk_specialist]


# ---------------------------------------------------------------------------
# 3. Mock the SDK Runner — feed canned specialist outputs
# ---------------------------------------------------------------------------


class _FakeRunResult:
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
# 4. Demo — invoke specialists directly and via the manager's tool
# ---------------------------------------------------------------------------


async def demo_invoke_agent_direct() -> None:
    """Path A: orchestrator code calls ``invoke_agent`` directly."""
    print("--- Demo A: invoke_agent direct (no LLM in the loop) ---")

    network = _StubNetwork()
    # In production: AgentMetadata.output_schema = "client_resources.signals.ValuationSignal".
    # We bypass the dotted-path allowlist here by hand-coercing inside
    # the stub Runner — the production path uses ``resolve_output_schema``.
    network.agent_metadata["valuation_specialist"] = AgentMetadata(
        exposed_to_user=False,
        output_schema=None,  # see comment above
    )

    canned = {
        # Stub Runner can already return a parsed BaseModel — mirrors
        # ``Agent(output_type=ValuationSignal)`` in the real SDK.
        "valuation_specialist": ValuationSignal(
            verdict="approve",
            fair_price=42.5,
            reasoning="P/E within target band.",
        ),
    }
    _patch_runner(canned)

    state = MultiAgentState()
    result = await invoke_agent(
        network.valuation_specialist,
        payload={"deal_id": "ACME-001", "exposure": 1_000_000},
        parent_state=state,
        network=network,
    )
    # ``invoke_agent`` records the result keyed by agent name.
    assert "valuation_specialist" in state.agent_calls
    print(f"  state.agent_calls keys: {sorted(state.agent_calls.keys())}")
    print(f"  invoke result: {result}")


async def demo_call_agent_tool() -> None:
    """Path B: manager LLM emits a ``call_agent`` tool call."""
    print("\n--- Demo B: build_call_agent_tool (whitelist enforced) ---")

    network = _StubNetwork()

    canned = {
        "risk_specialist": RiskSignal(
            verdict="approve",
            risk_score=22,
            reasoning="Counterparty rated A; collateral above SLA.",
        ),
    }
    _patch_runner(canned)

    # Build the tool the network factory would attach to network.manager.
    tool = build_call_agent_tool(network, caller_name="manager")
    network.manager.tools.append(tool)

    # Invoke the tool's underlying coroutine directly — in production the
    # SDK ``Runner`` plumbs this when the LLM emits a ``call_agent`` call.
    inner = tool.on_invoke_tool  # callable installed by @function_tool
    serialised = await inner(
        None,  # the SDK passes a RunContext; ignored by the stub-only path.
        '{"name": "risk_specialist", "payload": {"deal_id": "ACME-001"}}',
    )
    # The risk_specialist has no output_schema set on AgentMetadata, so
    # the tool wraps the raw text in {"text": "..."} per the uniform
    # contract documented in atendentepro/multiagent/tools.py. To get
    # the BaseModel JSON shape (``{"verdict": ..., "risk_score": ...}``)
    # declare ``output_schema: client_resources.signals.RiskSignal`` in
    # ``multiagent_config.yaml``.
    print(f"  manager received: {serialised}")
    assert '"text"' in serialised
    assert "approve" in serialised


async def demo_call_agent_forbidden() -> None:
    """Path C: whitelist violation surfaces as ``CallAgentForbidden``."""
    print("\n--- Demo C: CallAgentForbidden when target is off-whitelist ---")

    network = _StubNetwork()
    # Tighten the whitelist so risk_specialist becomes forbidden.
    network.agent_metadata["manager"] = AgentMetadata(
        can_call=["valuation_specialist"],  # risk_specialist removed on purpose
        builtin_tools=["call_agent"],
    )
    _patch_runner({})  # no agent should actually be invoked

    tool = build_call_agent_tool(network, caller_name="manager")
    inner = tool.on_invoke_tool

    try:
        await inner(
            None,
            '{"name": "risk_specialist", "payload": {}}',
        )
    except CallAgentForbidden as exc:
        print(f"  caught CallAgentForbidden: {exc}")
    else:
        raise AssertionError("expected CallAgentForbidden, got nothing")


async def main() -> None:
    await demo_invoke_agent_direct()
    await demo_call_agent_tool()
    await demo_call_agent_forbidden()
    print("\nOK — multi-agent hierarchy demo finished.")


if __name__ == "__main__":
    asyncio.run(main())
