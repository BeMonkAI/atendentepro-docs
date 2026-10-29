# -*- coding: utf-8 -*-
"""
Exemplo: Um único provider externo com modelos diferentes por agente.

Usa DeepSeek para todos os agentes, com deepseek-chat para tarefas
simples e deepseek-reasoner para tarefas que exigem raciocínio.

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    DEEPSEEK_API_KEY=sk-...
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network, ProviderConfig
from agents import Runner

# 1. Ativar licenca
activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

# 2. Configurar fallback global
configure(provider="openai", default_model="gpt-4.1-mini")

# 3. Definir providers por agente
#    - ProviderConfig resolve base_url e api_key via KNOWN_PROVIDERS + env vars
#    - Nao precisa passar api_key nem base_url para provedores conhecidos
AGENT_PROVIDERS = {
    # Roteamento — modelo leve
    "triage":       ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "flow":         ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "feedback":     ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "usage":        ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "onboarding":   ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "interview":    ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "confirmation": ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "escalation":   ProviderConfig(provider="deepseek", model="deepseek-chat"),

    # Respostas — modelo com raciocínio avançado
    "knowledge": ProviderConfig(provider="deepseek", model="deepseek-reasoner"),
    "answer":    ProviderConfig(provider="deepseek", model="deepseek-reasoner"),
}


async def main():
    # 4. Criar rede com providers por agente
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
        agent_providers=AGENT_PROVIDERS,
    )

    # 5. Executar
    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Quais são os planos disponíveis?"}],
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
