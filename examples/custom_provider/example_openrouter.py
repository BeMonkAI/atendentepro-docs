# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com OpenRouter (gateway multi-provider)

OpenRouter permite usar modelos de diferentes providers (Anthropic, Google, Meta, etc.)
atraves de uma unica API OpenAI-compatible.

Requisitos:
- Conta no OpenRouter (https://openrouter.ai)
- API key do OpenRouter

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=https://openrouter.ai/api/v1
    CUSTOM_API_KEY=sk-or-...
    DEFAULT_MODEL=anthropic/claude-sonnet-4
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network
from agents import Runner

activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# OpenRouter como gateway — escolha qualquer modelo disponivel
configure(
    provider="custom",
    custom_api_key=os.getenv("CUSTOM_API_KEY"),
    custom_base_url="https://openrouter.ai/api/v1",
    default_model="anthropic/claude-sonnet-4",  # ou "google/gemini-2.0-flash", "meta-llama/llama-3.1-70b-instruct", etc.
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Quais servicos voces oferecem?"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
