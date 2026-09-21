# -*- coding: utf-8 -*-
"""
Exemplo: Híbrido — agent_providers + agent_models combinados.

Demonstra como usar os dois mecanismos juntos:
  - agent_providers: agentes críticos com provider dedicado
  - agent_models: demais agentes com modelo específico no provider global

Ordem de resolução:
  1. agent_providers (ProviderConfig → Model instance)
  2. agent_models (string → usa provider global)
  3. default_model (fallback global)

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_API_KEY=sk-...
    DEEPSEEK_API_KEY=sk-...
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network, ProviderConfig
from agents import Runner

activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# Provider global: OpenAI (usado por agent_models e como fallback)
configure(provider="openai", default_model="gpt-4.1-mini")

# Apenas agentes críticos usam provider dedicado (DeepSeek)
AGENT_PROVIDERS = {
    "knowledge": ProviderConfig(provider="deepseek", model="deepseek-reasoner"),
    "answer":    ProviderConfig(provider="deepseek", model="deepseek-chat"),
}

# Demais agentes: modelo específico no provider global (OpenAI)
AGENT_MODELS = {
    "triage":       "gpt-4.1-mini",
    "flow":         "gpt-4.1-mini",
    "interview":    "gpt-4.1-mini",
    "confirmation": "gpt-4.1-mini",
    "escalation":   "gpt-4.1-mini",
    "feedback":     "gpt-4.1-nano",
    "usage":        "gpt-4.1-nano",
}

# Resultado:
#   knowledge → agent_providers → DeepSeek deepseek-reasoner
#   answer    → agent_providers → DeepSeek deepseek-chat
#   triage    → agent_models    → OpenAI gpt-4.1-mini
#   feedback  → agent_models    → OpenAI gpt-4.1-nano
#   onboarding→ (nenhum)        → OpenAI gpt-4.1-mini (default)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
        agent_providers=AGENT_PROVIDERS,
        agent_models=AGENT_MODELS,
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Gostaria de saber sobre a garantia"}],
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
