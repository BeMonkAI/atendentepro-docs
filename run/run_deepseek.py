#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com DeepSeek — modelos diferentes por agente

Usa ProviderConfig nativo para configurar DeepSeek em todos os agentes.
Agentes de roteamento usam deepseek-chat (barato), agentes de resposta
usam deepseek-reasoner (mais potente com chain-of-thought).

Requer:
    DEEPSEEK_API_KEY=sk-...  (chave da API DeepSeek)

    Ou passe api_key direto no ProviderConfig:
    ProviderConfig(provider="deepseek", model="deepseek-chat", api_key="sk-...")
"""

import asyncio
from pathlib import Path

from atendentepro import create_standard_network, configure, ProviderConfig
from agents import Runner


AGENT_PROVIDERS = {
    # Roteamento — modelo leve e barato
    "triage":     ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "flow":       ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "feedback":   ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "usage":      ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "onboarding": ProviderConfig(provider="deepseek", model="deepseek-chat"),

    # Respostas — raciocinio avancado (chain-of-thought)
    "knowledge": ProviderConfig(provider="deepseek", model="deepseek-reasoner"),
    "answer":    ProviderConfig(provider="deepseek", model="deepseek-reasoner"),

    # Intermediarios
    "interview":    ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "confirmation": ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "escalation":   ProviderConfig(provider="deepseek", model="deepseek-chat"),
}


async def main():
    # Fallback global (usado apenas se algum agente nao tiver ProviderConfig)
    configure(provider="openai", default_model="gpt-4.1-mini")

    templates_root = Path(__file__).parent.parent / "client_templates"

    print("Criando rede com DeepSeek...")
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        agent_providers=AGENT_PROVIDERS,
    )

    print("Rede criada!\n")
    print(f"  {'Agente':<16} {'Modelo'}")
    print(f"  {'-'*16} {'-'*24}")
    for name, pc in AGENT_PROVIDERS.items():
        print(f"  {name:<16} {pc.model}")

    print("\nDigite 'sair' para encerrar.\n")
    messages = []

    while True:
        try:
            user_input = input("Voce: ").strip()
            if user_input.lower() in ("sair", "exit", "quit", "q"):
                print("Ate logo!")
                break
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            result = await Runner.run(network.triage, messages)
            response = str(result.final_output) if result.final_output else "..."
            print(f"Assistente: {response}\n")
            messages.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            print("\nAte logo!")
            break
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("  AtendentePro - DeepSeek Multi-Model")
    print("=" * 50)
    asyncio.run(main())
