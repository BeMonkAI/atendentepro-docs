# -*- coding: utf-8 -*-
"""
Exemplo: Embeddings com Google Gemini

O endpoint OpenAI-compatible do Gemini suporta embeddings via /v1/embeddings.
O modelo de embedding do Gemini e o text-embedding-004.

Requisitos:
- API key do Google AI Studio (https://aistudio.google.com/apikey)

Modelos de embedding disponiveis:
    - text-embedding-004  (768 dims, recomendado)

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
    CUSTOM_API_KEY=sua-chave-gemini
    DEFAULT_MODEL=gemini-2.0-flash
    EMBEDDING_MODEL=text-embedding-004
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
    custom_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    default_model="gemini-2.0-flash",
    embedding_model="text-embedding-004",
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Buscar informacoes sobre garantia do produto"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
