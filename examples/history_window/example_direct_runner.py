# -*- coding: utf-8 -*-
"""Quem chama Runner.run direto (sem run_with_memory) precisa aplicar a janela.

``run_with_memory`` chama ``apply_history_window`` automaticamente. Quem
prefere o caminho direto (``Runner.run(agent, messages)``) deve invocar
o helper antes para que a janela seja respeitada.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from atendentepro import HistoryWindow, apply_history_window


class _StubAgent:
    name = "Triage Agent"


class _StubResult:
    final_output = "ok"


async def _stub_runner_run(agent: Any, messages: List[Dict[str, Any]]) -> Any:
    """Stub do agents.Runner.run para o exemplo nao precisar de credenciais."""
    print(f"  Runner.run recebeu {len(messages)} mensagens (apos janela)")
    return _StubResult()


class _StubNetwork:
    triage = _StubAgent()
    history_window: Any = None


async def main() -> None:
    network = _StubNetwork()
    network.history_window = HistoryWindow(max_messages=5)

    # Histórico longo do tenant
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": "voce e atendente"},
    ]
    for i in range(20):
        messages.append({"role": "user", "content": f"u{i}"})
        messages.append({"role": "assistant", "content": f"a{i}"})
    print(f"Original: {len(messages)} mensagens")

    # Caminho recomendado: aplicar janela antes do Runner.run.
    # apply_history_window e async desde a v0.20.0 (Phase 4.2) — precisa await.
    windowed = await apply_history_window(network, messages)
    print(f"Apos apply_history_window: {len(windowed)} mensagens")

    # Em producao, substitua _stub_runner_run por:
    #   from agents import Runner
    #   result = await Runner.run(network.triage, windowed)
    result = await _stub_runner_run(network.triage, windowed)
    print(f"Resultado: {result.final_output}")

    print("\nOK — janela aplicada antes do Runner.run direto.")


if __name__ == "__main__":
    asyncio.run(main())
