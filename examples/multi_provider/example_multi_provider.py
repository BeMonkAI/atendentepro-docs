# -*- coding: utf-8 -*-
"""
Exemplo: 4 provedores simultâneos no mesmo sistema.

Cada agente usa o provedor mais adequado ao seu papel:
  - OpenAI:    triage, flow (roteamento rápido, baixa latência)
  - DeepSeek:  knowledge, answer (raciocínio profundo, custo baixo)
  - Gemini:    interview, onboarding (contexto longo, multimodal)
  - Anthropic: confirmation, escalation (instruções complexas, safety)

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_API_KEY=sk-...
    DEEPSEEK_API_KEY=sk-...
    GEMINI_API_KEY=...
    ANTHROPIC_API_KEY=sk-ant-...
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network, ProviderConfig
from agents import Runner

# 1. Ativar
activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# 2. Fallback global (agentes sem ProviderConfig usam este)
configure(provider="openai", default_model="gpt-4.1-mini")

# 3. Cada agente com seu provider
AGENT_PROVIDERS = {
    # OpenAI — latência baixa, bom em classificação
    "triage":   ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "flow":     ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "feedback": ProviderConfig(provider="openai", model="gpt-4.1-nano"),

    # DeepSeek — raciocínio chain-of-thought, custo baixo
    "knowledge": ProviderConfig(provider="deepseek", model="deepseek-reasoner"),
    "answer":    ProviderConfig(provider="deepseek", model="deepseek-chat"),

    # Gemini — contexto longo (1M tokens), multimodal
    "interview":  ProviderConfig(provider="gemini", model="gemini-2.5-pro"),
    "onboarding": ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "usage":      ProviderConfig(provider="gemini", model="gemini-2.0-flash"),

    # Claude — segue instruções complexas, safety forte
    "confirmation": ProviderConfig(provider="anthropic", model="claude-sonnet-4-6-20250514"),
    "escalation":   ProviderConfig(provider="anthropic", model="claude-sonnet-4-6-20250514"),
}


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
        agent_providers=AGENT_PROVIDERS,
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Preciso de ajuda com meu pedido #12345"}],
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
