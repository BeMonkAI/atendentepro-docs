# -*- coding: utf-8 -*-
"""
Exemplo: Embeddings com Jina AI

Jina AI oferece modelos de embedding de alta qualidade via API OpenAI-compatible.
Neste exemplo, usamos Jina apenas para embeddings enquanto o chat usa outro provider.

Requisitos:
- API key da Jina AI (https://jina.ai/embeddings)

Modelos de embedding disponiveis:
    - jina-embeddings-v3       (1024 dims, multilingue, SOTA)
    - jina-embeddings-v2-base-en (768 dims, ingles)

Nota importante:
    Jina AI so fornece embeddings, nao chat. Este exemplo mostra como
    usar Jina para embeddings enquanto o chat roda em outro provider.
    Para isso, voce precisa gerar os embeddings offline com o client Jina
    e usar o Knowledge Agent sem RAG automatico, ou manter OpenAI/Azure
    como provider principal e trocar apenas o embedding_model.

Opcao 1 - OpenAI como chat + Jina como embedding (via env):
    OPENAI_API_KEY=sk-openai...
    EMBEDDING_MODEL=text-embedding-3-large
    # (Jina nao e compativel como custom provider pois nao tem /chat/completions)

Opcao 2 - Gerar embeddings offline com Jina e carregar no Knowledge Agent:
    pip install jina-embeddings
    # Gerar embeddings e salvar como .pkl

Este exemplo mostra a Opcao 1 adaptada: usando OpenAI para tudo
mas trocando para um embedding menor e mais barato.

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_API_KEY=sk-sua-chave-openai
    EMBEDDING_MODEL=text-embedding-3-small
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network
from agents import Runner

activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# Usar OpenAI com embedding model menor e mais barato
configure(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    default_model="gpt-4.1-mini",
    embedding_model="text-embedding-3-small",
)


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Buscar na base de conhecimento sobre politica de troca"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
