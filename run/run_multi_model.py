#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com modelos diferentes por agente

Demonstra como usar agent_models para atribuir modelos distintos
a cada agente, otimizando custo vs qualidade:

- Triage/Flow/Feedback: modelo leve (gpt-4.1-mini) — tarefas de roteamento
- Knowledge/Answer: modelo potente (gpt-4.1) — respostas que exigem precisao
- Interview/Confirmation: modelo intermediario (gpt-4.1-mini)
"""

import asyncio
from pathlib import Path

from atendentepro import create_standard_network, configure
from agents import Runner


# Mapeamento de modelos por agente
AGENT_MODELS = {
    # Agentes de roteamento — modelo leve, rapido e barato
    "triage": "gpt-4.1-mini",
    "flow": "gpt-4.1-mini",
    "feedback": "gpt-4.1-mini",
    "usage": "gpt-4.1-mini",
    "onboarding": "gpt-4.1-mini",

    # Agentes de resposta — modelo potente para qualidade
    "knowledge": "gpt-4.1",
    "answer": "gpt-4.1",

    # Agentes intermediarios
    "interview": "gpt-4.1-mini",
    "confirmation": "gpt-4.1-mini",
    "escalation": "gpt-4.1-mini",
}


async def main():
    """Executa AtendentePro com modelos diferentes por agente."""

    # 1. Configurar provider (default_model serve como fallback)
    configure(provider="openai", default_model="gpt-4.1-mini")

    # 2. Criar rede com modelos por agente
    templates_root = Path(__file__).parent.parent / "client_templates"

    print("Criando rede com modelos por agente...")
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        agent_models=AGENT_MODELS,
    )

    # 3. Mostrar configuracao
    print("Rede criada com sucesso!\n")
    print(f"  {'Agente':<16} {'Modelo'}")
    print(f"  {'-'*16} {'-'*20}")
    for name, model in AGENT_MODELS.items():
        print(f"  {name:<16} {model}")

    # 4. Conversa interativa
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
    print("  AtendentePro - Multi-Model Example")
    print("=" * 50)
    asyncio.run(main())
