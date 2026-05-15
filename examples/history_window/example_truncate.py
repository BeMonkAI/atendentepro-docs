# -*- coding: utf-8 -*-
"""Truncamento simples — Phase 4.1 (ativo na v0.19.0).

Demonstra ``max_messages`` cortando o histórico antes de chegar ao LLM.
Não faz chamada LLM real — usa um stub de Runner.run.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from atendentepro import HistoryWindow, apply_history_window


def _build_long_conversation(n_turns: int = 30) -> List[Dict[str, Any]]:
    """Simula uma conversa multi-turn longa com mensagem system de memoria."""
    msgs: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": "Memória relevante: cliente Premium, ja resolveu 3 chamados.",
        }
    ]
    for i in range(n_turns):
        msgs.append({"role": "user", "content": f"pergunta {i}"})
        msgs.append({"role": "assistant", "content": f"resposta {i}"})
    return msgs


class _StubNetwork:
    """Substitui AgentNetwork para o exemplo nao precisar de license/templates."""

    history_window: Any = None


async def main() -> None:
    network = _StubNetwork()
    network.history_window = HistoryWindow(max_messages=10)

    messages = _build_long_conversation(n_turns=30)
    print(f"Original: {len(messages)} mensagens (1 system + 60 user/assistant)")

    windowed = await apply_history_window(network, messages)
    print(f"Janela aplicada: {len(windowed)} mensagens")
    print(f"  - System preservadas: {sum(1 for m in windowed if m['role'] == 'system')}")
    print(f"  - User/assistant: {sum(1 for m in windowed if m['role'] != 'system')}")

    # As ultimas 10 user/assistant + a system inicial ainda vao para o LLM.
    assert len(windowed) == 11
    assert windowed[0]["role"] == "system"
    assert windowed[-1]["content"] == "resposta 29"
    print("\nOK — truncamento aplicado conforme esperado.")


if __name__ == "__main__":
    asyncio.run(main())
