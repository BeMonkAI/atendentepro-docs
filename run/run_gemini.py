#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com Google Gemini — modelos diferentes por agente

Usa ProviderConfig nativo para configurar Gemini em todos os agentes.
Agentes de roteamento usam gemini-2.0-flash (rapido), agentes de
resposta usam gemini-2.5-pro (mais capaz, contexto de 1M tokens).

Requer:
    GEMINI_API_KEY=...  (chave da API Google AI Studio)

    Ou passe api_key direto no ProviderConfig:
    ProviderConfig(provider="gemini", model="gemini-2.0-flash", api_key="...")
"""

import asyncio
from pathlib import Path

from atendentepro import create_standard_network, configure, ProviderConfig
from agents import Runner


AGENT_PROVIDERS = {
    # Roteamento — flash (rapido e barato)
    "triage":     ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "flow":       ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "feedback":   ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "usage":      ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "onboarding": ProviderConfig(provider="gemini", model="gemini-2.0-flash"),

    # Respostas — pro (mais capaz, contexto longo)
    "knowledge": ProviderConfig(provider="gemini", model="gemini-2.5-pro"),
    "answer":    ProviderConfig(provider="gemini", model="gemini-2.5-pro"),

    # Intermediarios — flash
    "interview":    ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "confirmation": ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "escalation":   ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
}


async def main():
    configure(provider="openai", default_model="gpt-4.1-mini")

    templates_root = Path(__file__).parent.parent / "client_templates"

    print("Criando rede com Google Gemini...")
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
    print("  AtendentePro - Google Gemini Multi-Model")
    print("=" * 50)
    asyncio.run(main())
