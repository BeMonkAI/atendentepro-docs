# -*- coding: utf-8 -*-
"""HistoryWindow — API completa com todos os 5 parametros.

Demonstra todos os campos de ``HistoryWindow``. **Os 5 parametros estao
ATIVOS desde a v0.21.0** (Phase 4.3). O cliente OpenAI-compativel e
stubado para o exemplo rodar sem API key.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from atendentepro import HistoryWindow, apply_history_window


# -----------------------------------------------------------------------------
# Phase 4.3 — callback (ATIVO desde v0.21.0)
# -----------------------------------------------------------------------------
def on_subagent_finish(agent_name: str, msgs: List[Dict[str, Any]]) -> None:
    """Limpeza custom quando o controle volta para o Triage.

    Recebe a lista de mensagens *mutavel* — caller pode editar in-place.
    Roda no inicio de cada turno quando ``network.last_agent_name`` e
    diferente de ``"Triage Agent"``.

    NOTA: a lista contem TODAS as mensagens, incluindo system messages
    no topo. Se voce quer preservar instrucoes / memoria, filtre
    explicitamente como abaixo.
    """
    if agent_name != "Knowledge Agent":
        return

    # Mantem system messages no topo + apenas os 2 ultimos turnos
    # nao-system para nao poluir a proxima pergunta com o bloco de RAG.
    head = [m for m in msgs if m.get("role") == "system"]
    rest = [m for m in msgs if m.get("role") != "system"]
    msgs[:] = head + rest[-2:]


# -----------------------------------------------------------------------------
# Configuracao completa
# -----------------------------------------------------------------------------
window = HistoryWindow(
    # PHASE 4.1 (ATIVO): trunca para os 20 ultimos itens user/assistant.
    max_messages=20,
    # PHASE 4.2 (ATIVO): condensa turnos antigos quando passar de 10.
    summarize_after_n_messages=10,
    # PHASE 4.2 (ATIVO): override do prompt usado na sumarizacao.
    summary_system_prompt=(
        "Voce resume turnos antigos de uma conversa de atendimento. "
        "Liste decisoes tomadas, fatos confirmados pelo usuario e "
        "pendencias em um unico paragrafo conciso em portugues. Nao "
        "invente informacao alem do historico fornecido."
    ),
    # PHASE 4.2 (ATIVO): modelo usado na chamada de sumarizacao.
    summary_model="gpt-4.1",
    # PHASE 4.3 (ATIVO): callback quando controle volta ao Triage.
    on_agent_reset=on_subagent_finish,
)


# Stub do cliente OpenAI-compativel para o exemplo nao precisar de API key.
# Em producao, ``apply_history_window`` resolve via ``atendentepro.utils.get_async_client()``.
class _StubChat:
    async def create(self, **kwargs: Any) -> Any:
        class _Msg:
            content = "Resumo do exemplo: usuario testou os 5 parametros."

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


class _StubClient:
    chat = type("X", (), {"completions": _StubChat()})()


class _StubNetwork:
    history_window: Any = None
    # apply_history_window consulta este atributo antes de get_async_client();
    # em producao, omita-o e a lib resolve sozinha.
    _summary_client = _StubClient()
    # last_agent_name simula o estado pos-turno: Knowledge respondeu antes,
    # agora controle volta para Triage -> on_agent_reset deve disparar.
    last_agent_name = "Knowledge Agent"


async def main() -> None:
    network = _StubNetwork()
    network.history_window = window

    print("HistoryWindow configurado com TODOS os 5 parametros.")
    print(f"  max_messages                = {window.max_messages}    [Phase 4.1 ATIVO]")
    print(
        f"  summarize_after_n_messages  = {window.summarize_after_n_messages}    [Phase 4.2 ATIVO]"
    )
    print(
        f"  summary_system_prompt       = <{len(window.summary_system_prompt)} chars> [Phase 4.2 ATIVO]"
    )
    print(f"  summary_model               = {window.summary_model!r} [Phase 4.2 ATIVO]")
    print(f"  on_agent_reset              = {window.on_agent_reset.__name__}   [Phase 4.3 ATIVO]")

    # Simula 30 turnos
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": "voce e um atendente"},
    ]
    for i in range(30):
        messages.append({"role": "user", "content": f"u{i}"})
        messages.append({"role": "assistant", "content": f"a{i}"})

    print(f"\nOriginal: {len(messages)} mensagens")

    # apply_history_window e async desde a v0.20.0 (Phase 4.2) — precisa await.
    out = await apply_history_window(network, messages)
    print(f"Apos janela:  {len(out)} mensagens")

    # Sequencia de operacoes:
    #  1. on_agent_reset (Phase 4.3): last_agent_name="Knowledge Agent" dispara
    #     o callback, que apaga tudo exceto os 2 ultimos turnos.
    #  2. summarize_after_n_messages=10: 2 itens < 10, nao sumariza.
    #  3. max_messages=20: 2 itens < 20, noop.
    # Resultado final: 1 system original + 2 turnos = 3 mensagens.
    assert len(out) == 3
    assert out[0]["role"] == "system"
    assert out[0]["content"] == "voce e um atendente"
    assert out[-1]["content"] == "a29"
    print("  -> on_agent_reset cortou para 2 ultimos turnos; nao precisou sumarizar nem truncar.")
    print("\nOK — todos os 5 parametros ATIVOS desde a v0.21.0.")


if __name__ == "__main__":
    asyncio.run(main())
