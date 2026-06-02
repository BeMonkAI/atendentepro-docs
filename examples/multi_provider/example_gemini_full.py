# -*- coding: utf-8 -*-
"""
Exemplo: 100% Gemini — todos os agentes no Gemini nativo.

Com o GeminiAdapter, é possível usar Gemini para TODOS os agentes,
incluindo guardrails (json_schema suportado) e RAG (embeddings nativos).

Diferença do modo "custom" com base_url OpenAI-compatible:
  - Modo custom:  configure(provider="custom", custom_base_url="https://generativelanguage.googleapis.com/v1beta/openai")
    → NÃO suporta json_schema, NÃO suporta embeddings
  - Modo nativo:  ProviderConfig(provider="gemini", model="gemini-2.0-flash")
    → Suporta TUDO via google-genai SDK

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

# 2. OpenAI como fallback (não será usado — todos os agentes têm ProviderConfig)
configure(provider="openai", default_model="gpt-4.1-mini")

# 3. Todos os agentes com Gemini nativo
gemini_flash = ProviderConfig(provider="gemini", model="gemini-2.0-flash")
gemini_pro = ProviderConfig(provider="gemini", model="gemini-2.5-pro")

AGENT_PROVIDERS = {
    "triage": gemini_flash,
    "flow": gemini_flash,
    "interview": gemini_pro,  # Contexto longo para entrevistas detalhadas
    "answer": gemini_flash,
    "knowledge": gemini_flash,  # Embeddings nativos — RAG funciona
    "confirmation": gemini_flash,
    "usage": gemini_flash,
    "escalation": gemini_flash,
    "feedback": gemini_flash,
}


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
        agent_providers=AGENT_PROVIDERS,
        # Guardrails funcionam normalmente — Gemini suporta structured output
        require_guardrails_config=True,
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Quero saber sobre o plano empresarial"}],
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
