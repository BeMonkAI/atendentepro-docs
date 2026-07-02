# -*- coding: utf-8 -*-
"""
Exemplo: Embeddings com vLLM (servidor local com GPU)

vLLM suporta embedding models via /v1/embeddings quando iniciado com um modelo
de embedding. Voce pode rodar o servidor de chat e embedding separadamente ou
usar um modelo que suporte ambos.

Requisitos:
- vLLM instalado com GPU
- Modelo de embedding baixado

Iniciar vLLM com modelo de embedding:
    python -m vllm.entrypoints.openai.api_server \
        --model BAAI/bge-large-en-v1.5 \
        --task embed \
        --port 8001

Iniciar vLLM com modelo de chat (porta separada):
    python -m vllm.entrypoints.openai.api_server \
        --model meta-llama/Llama-3.1-8B-Instruct \
        --port 8000

Modelos de embedding populares no vLLM:
    - BAAI/bge-large-en-v1.5   (1024 dims)
    - BAAI/bge-m3              (1024 dims, multilingue)
    - intfloat/e5-large-v2     (1024 dims)
    - intfloat/multilingual-e5-large (1024 dims, multilingue)

Nota: Neste exemplo, chat e embeddings usam o mesmo endpoint.
      Se voce rodar em portas diferentes, configure o embedding_model
      com o nome do modelo de embedding e ajuste conforme necessario.

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=http://localhost:8000/v1
    CUSTOM_API_KEY=vllm
    DEFAULT_MODEL=meta-llama/Llama-3.1-8B-Instruct
    EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
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
    custom_api_key="vllm",
    custom_base_url="http://localhost:8000/v1",
    default_model="meta-llama/Llama-3.1-8B-Instruct",
    embedding_model="BAAI/bge-large-en-v1.5",
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Preciso de informacoes sobre o contrato"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
