# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com Ollama (modelos locais)

Requisitos:
- Ollama instalado e rodando (https://ollama.ai)
- Modelo baixado: ollama pull llama3.1

Iniciar Ollama:
    ollama serve

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=http://localhost:11434/v1
    CUSTOM_API_KEY=ollama
    DEFAULT_MODEL=llama3.1
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network
from agents import Runner

activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# Ollama roda local — api_key pode ser qualquer string nao-vazia
configure(
    provider="custom",
    custom_api_key="ollama",  # Ollama nao valida a key, mas o campo e obrigatorio
    custom_base_url="http://localhost:11434/v1",
    default_model="llama3.1",  # ou "mistral", "gemma2", "qwen2.5", etc.
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Ola, quero saber sobre meu pedido"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
