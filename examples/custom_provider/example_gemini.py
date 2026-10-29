# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com Google Gemini (endpoint OpenAI-compatible)

Requisitos:
- API key do Google AI Studio (https://aistudio.google.com/apikey)

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
    CUSTOM_API_KEY=sua-chave-gemini
    DEFAULT_MODEL=gemini-2.0-flash
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network
from agents import Runner

# 1. Ativar licenca
activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# 2. Configurar Gemini como provider
configure(
    provider="custom",
    custom_api_key=os.getenv("CUSTOM_API_KEY"),
    custom_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    default_model="gemini-2.0-flash",  # ou "gemini-2.5-pro", "gemini-2.5-flash"
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Quais sao as opcoes de plano?"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
