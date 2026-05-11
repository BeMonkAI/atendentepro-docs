# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com vLLM (servidor local de inferencia)

Requisitos:
- vLLM instalado e rodando com um modelo
- GPU com VRAM suficiente para o modelo

Iniciar vLLM:
    python -m vllm.entrypoints.openai.api_server \
        --model meta-llama/Llama-3.1-8B-Instruct \
        --port 8000

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=http://localhost:8000/v1
    CUSTOM_API_KEY=vllm
    DEFAULT_MODEL=meta-llama/Llama-3.1-8B-Instruct
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
    custom_api_key="vllm",  # vLLM nao valida a key por padrao
    custom_base_url="http://localhost:8000/v1",
    default_model="meta-llama/Llama-3.1-8B-Instruct",
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Preciso de ajuda com o produto"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
