# -*- coding: utf-8 -*-
"""
Exemplo: Configuracao do custom provider via variaveis de ambiente

Neste exemplo, nenhum parametro e passado ao configure() — tudo vem do .env.
Isso e util para deploy em producao onde as credenciais ficam no ambiente.

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=https://api.deepseek.com/v1
    CUSTOM_API_KEY=sk-...
    DEFAULT_MODEL=deepseek-chat
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, create_standard_network, get_config
from agents import Runner

# 1. Ativar licenca
activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# 2. Verificar que as variaveis de ambiente foram carregadas
config = get_config()
print(f"Provider: {config.provider}")
print(f"Base URL: {config.custom_base_url}")
print(f"Model:    {config.default_model}")
assert config.provider == "custom", "OPENAI_PROVIDER deve ser 'custom' no .env"
assert config.custom_base_url, "CUSTOM_BASE_URL deve estar definida no .env"
assert config.custom_api_key, "CUSTOM_API_KEY deve estar definida no .env"


async def main():
    # 3. Criar rede — o client custom e criado automaticamente a partir do config
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
    )

    # 4. Executar
    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Ola!"}],
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
