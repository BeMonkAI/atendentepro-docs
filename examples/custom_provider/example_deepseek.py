# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com DeepSeek

Requisitos:
- Conta na DeepSeek (https://platform.deepseek.com)
- API key da DeepSeek

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=https://api.deepseek.com/v1
    CUSTOM_API_KEY=sk-sua-chave-deepseek
    DEFAULT_MODEL=deepseek-chat
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

# 2. Configurar DeepSeek como provider
configure(
    provider="custom",
    custom_api_key=os.getenv("CUSTOM_API_KEY", "sk-..."),
    custom_base_url="https://api.deepseek.com/v1",
    default_model="deepseek-chat",  # ou "deepseek-reasoner" para o R1
)


async def main():
    # 3. Criar rede de agentes (funciona identicamente ao OpenAI)
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    # 4. Executar conversa
    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Ola, preciso de ajuda com meu pedido"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
