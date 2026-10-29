# -*- coding: utf-8 -*-
"""
Exemplo: Otimização de custo com multi-provider.

Estratégia: usar o modelo mais barato possível para cada tarefa.

  Tier 1 (Nano):  triage, feedback, usage        — ~$0.10/M tokens
  Tier 2 (Mini):  flow, interview, confirmation   — ~$0.40/M tokens
  Tier 3 (Pro):   knowledge, answer               — ~$0.27/M tokens (DeepSeek)

Economia estimada: ~77% vs usar gpt-4.1 em tudo.

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_API_KEY=sk-...
    DEEPSEEK_API_KEY=sk-...
    GEMINI_API_KEY=...
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network, ProviderConfig
from agents import Runner

activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))
configure(provider="openai", default_model="gpt-4.1-nano")

AGENT_PROVIDERS = {
    # TIER 1 — Nano/Flash: classificação simples (~$0.10/M tokens)
    "triage":   ProviderConfig(provider="openai", model="gpt-4.1-nano"),
    "feedback": ProviderConfig(provider="openai", model="gpt-4.1-nano"),
    "usage":    ProviderConfig(provider="gemini", model="gemini-2.0-flash"),

    # TIER 2 — Mini: algum raciocínio necessário (~$0.40/M tokens)
    "flow":         ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "interview":    ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "confirmation": ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "onboarding":   ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "escalation":   ProviderConfig(provider="openai", model="gpt-4.1-mini"),

    # TIER 3 — Pro: respostas ao usuário final (~$0.27/M tokens)
    "knowledge": ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "answer":    ProviderConfig(provider="deepseek", model="deepseek-chat"),
}


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
        agent_providers=AGENT_PROVIDERS,
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Quanto custa o plano premium?"}],
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
