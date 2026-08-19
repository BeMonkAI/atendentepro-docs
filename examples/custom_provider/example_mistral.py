# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com Mistral AI

Requisitos:
- API key da Mistral (https://console.mistral.ai)

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=https://api.mistral.ai/v1
    CUSTOM_API_KEY=sua-chave-mistral
    DEFAULT_MODEL=mistral-large-latest
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
    custom_base_url="https://api.mistral.ai/v1",
    default_model="mistral-large-latest",  # ou "mistral-small-latest", "codestral-latest"
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Gostaria de fazer uma reclamacao"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
