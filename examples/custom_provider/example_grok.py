# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com xAI Grok

Requisitos:
- API key da xAI (https://console.x.ai)

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=https://api.x.ai/v1
    CUSTOM_API_KEY=xai-sua-chave
    DEFAULT_MODEL=grok-3-latest
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
    custom_base_url="https://api.x.ai/v1",
    default_model="grok-3-latest",  # ou "grok-3-mini-latest"
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Como funciona o suporte tecnico?"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
