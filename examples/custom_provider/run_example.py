# -*- coding: utf-8 -*-
"""
Script para testar o custom provider.

Uso:
    python docs/examples/custom_provider/run_example.py

Configura o provider a partir das variaveis de ambiente e executa
uma conversa simples com o agente triage.

Variaveis necessarias no .env:
    ATENDENTEPRO_LICENSE_KEY=ATP_...
    OPENAI_PROVIDER=custom
    CUSTOM_BASE_URL=...       (ex.: https://api.deepseek.com/v1)
    CUSTOM_API_KEY=...
    DEFAULT_MODEL=...         (ex.: deepseek-chat)
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Verificar variaveis obrigatorias
required = ["ATENDENTEPRO_LICENSE_KEY", "CUSTOM_BASE_URL", "CUSTOM_API_KEY"]
missing = [v for v in required if not os.getenv(v)]
if missing:
    print(f"Variaveis faltando no .env: {', '.join(missing)}")
    print("Consulte o README.md deste diretorio para exemplos de configuracao.")
    sys.exit(1)

from atendentepro import activate, configure, create_standard_network, get_config
from agents import Runner

# Ativar
activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# Configurar (le automaticamente do .env se OPENAI_PROVIDER=custom)
config = get_config()
print(f"Provider:  {config.provider}")
print(f"Base URL:  {config.custom_base_url}")
print(f"Model:     {config.default_model}")
print()

# Usar templates standard incluidos no repositorio
templates_root = Path(__file__).resolve().parent.parent.parent.parent / "templates"
client_name = "standard"

if not (templates_root / client_name).exists():
    print(f"Pasta de templates nao encontrada: {templates_root / client_name}")
    print("Ajuste templates_root e client_name para seu projeto.")
    sys.exit(1)


async def main():
    network = create_standard_network(
        templates_root=templates_root,
        client=client_name,
    )

    messages = [
        {"role": "user", "content": "Ola, quero saber mais sobre os servicos disponiveis"},
    ]

    print("Enviando mensagem ao triage...")
    result = await Runner.run(network.triage, messages)
    print(f"\nResposta:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
