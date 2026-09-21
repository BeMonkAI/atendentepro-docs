# -*- coding: utf-8 -*-
"""
Exemplo: Embeddings com Ollama (100% local, sem custo)

Ollama suporta modelos de embedding via endpoint /v1/embeddings.
Como o provider custom usa o mesmo client para chat e embeddings,
basta configurar o embedding_model com um modelo suportado pelo Ollama.

Requisitos:
- Ollama instalado e rodando (https://ollama.ai)
- Modelos baixados:
    ollama pull llama3.1
    ollama pull nomic-embed-text

Iniciar Ollama:
    ollama serve

Modelos de embedding disponiveis no Ollama:
    - nomic-embed-text    (768 dims, bom custo-beneficio)
    - mxbai-embed-large   (1024 dims, melhor qualidade)
    - all-minilm          (384 dims, mais leve)
    - snowflake-arctic-embed (1024 dims)

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=http://localhost:11434/v1
    CUSTOM_API_KEY=ollama
    DEFAULT_MODEL=llama3.1
    EMBEDDING_MODEL=nomic-embed-text
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
    custom_api_key="ollama",
    custom_base_url="http://localhost:11434/v1",
    default_model="llama3.1",
    embedding_model="nomic-embed-text",
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Quais documentos voces tem sobre o produto?"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
