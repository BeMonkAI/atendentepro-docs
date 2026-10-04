# -*- coding: utf-8 -*-
"""
Exemplo: Embeddings via OpenRouter

OpenRouter e um gateway multi-provider que tambem suporta embeddings
via endpoint /v1/embeddings. Voce pode usar modelos de embedding de
diferentes providers atraves de uma unica API key.

Requisitos:
- Conta no OpenRouter (https://openrouter.ai)
- API key do OpenRouter

Modelos de embedding disponiveis no OpenRouter:
    - openai/text-embedding-3-small    (1536 dims)
    - openai/text-embedding-3-large    (3072 dims)
    - openai/text-embedding-ada-002    (1536 dims, legacy)

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=https://openrouter.ai/api/v1
    CUSTOM_API_KEY=sk-or-...
    DEFAULT_MODEL=anthropic/claude-sonnet-4
    EMBEDDING_MODEL=openai/text-embedding-3-small
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network
from agents import Runner

activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

configure(
    provider="custom",
    custom_api_key=os.getenv("CUSTOM_API_KEY"),
    custom_base_url="https://openrouter.ai/api/v1",
    default_model="anthropic/claude-sonnet-4",
    embedding_model="openai/text-embedding-3-small",
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Consultar base de conhecimento sobre prazos"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
