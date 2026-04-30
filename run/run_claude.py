#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com Anthropic Claude — modelos diferentes por agente

Usa ProviderConfig nativo para configurar Claude em todos os agentes.
Agentes de roteamento usam claude-haiku (rapido e barato), agentes de
resposta usam claude-sonnet (equilibrio custo/qualidade).

Requer:
    ANTHROPIC_API_KEY=sk-ant-...  (chave da API Anthropic)

    Ou passe api_key direto no ProviderConfig:
    ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001", api_key="sk-ant-...")
"""

import asyncio
from pathlib import Path

from atendentepro import create_standard_network, configure, ProviderConfig
from agents import Runner


AGENT_PROVIDERS = {
    # Roteamento — haiku (rapido e barato)
    "triage":     ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001"),
    "flow":       ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001"),
    "feedback":   ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001"),
    "usage":      ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001"),
    "onboarding": ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001"),

    # Respostas — sonnet (equilibrio custo/qualidade)
    "knowledge": ProviderConfig(provider="anthropic", model="claude-sonnet-4-6-20250514"),
    "answer":    ProviderConfig(provider="anthropic", model="claude-sonnet-4-6-20250514"),

    # Intermediarios — haiku
    "interview":    ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001"),
    "confirmation": ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001"),
    "escalation":   ProviderConfig(provider="anthropic", model="claude-haiku-4-5-20251001"),
}


async def main():
    configure(provider="openai", default_model="gpt-4.1-mini")

    templates_root = Path(__file__).parent.parent / "client_templates"

    print("Criando rede com Anthropic Claude...")
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        agent_providers=AGENT_PROVIDERS,
    )

    print("Rede criada!\n")
    print(f"  {'Agente':<16} {'Modelo'}")
    print(f"  {'-'*16} {'-'*32}")
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
    print("  AtendentePro - Anthropic Claude Multi-Model")
    print("=" * 50)
    asyncio.run(main())
