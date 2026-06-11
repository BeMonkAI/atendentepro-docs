# -*- coding: utf-8 -*-
"""
Exemplo: Gemini como provider nativo via GeminiAdapter.

O GeminiAdapter usa o SDK google-genai nativo, oferecendo:
  - Suporte completo a function calling (handoffs entre agentes)
  - Structured output via response_schema (guardrails funcionam)
  - Embeddings nativos (RAG funciona sem provider separado)
  - Contexto longo (1M tokens no Gemini 2.5 Pro)

Comparado ao modo OpenAI-compatible (base_url), o adapter nativo:
  - Suporta json_schema (guardrails com output_type)
  - Suporta embeddings (sem precisar de OpenAI separado para RAG)
  - Melhor handling de tool_choice e function calling

Requisitos:
    pip install atendentepro[gemini]

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    GEMINI_API_KEY=...
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from agents import Runner

from atendentepro import ProviderConfig, activate, configure, create_standard_network

# 1. Ativar
activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# 2. Gemini como provider global
configure(provider="openai", default_model="gpt-4.1-mini")

# 3. Usar Gemini nativo para agentes específicos
AGENT_PROVIDERS = {
    "triage": ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "flow": ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "interview": ProviderConfig(provider="gemini", model="gemini-2.5-pro"),
    "answer": ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "knowledge": ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
}


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
        agent_providers=AGENT_PROVIDERS,
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Como funciona o plano premium?"}],
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
