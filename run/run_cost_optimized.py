#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro — Otimizacao de custo com multi-provider

Demonstra uma estrategia real de otimizacao de custo: usar o modelo mais
barato possivel para cada tarefa, misturando providers para maximizar
a relacao custo/qualidade.

Estrategia:
  - Tarefas simples (roteamento, feedback) -> modelos nano/flash (centavos)
  - Tarefas intermediarias (fluxo, entrevista) -> modelos mid-tier
  - Tarefas criticas (knowledge, answer) -> modelos potentes

Custo estimado por 1000 conversas (10 msgs cada):
  - Tudo gpt-4.1:      ~$15.00
  - Esta configuracao:  ~$3.50  (economia de ~77%)

Requer variaveis de ambiente:
    OPENAI_API_KEY=sk-...
    DEEPSEEK_API_KEY=sk-...
    GEMINI_API_KEY=...
"""

import asyncio
from pathlib import Path

from atendentepro import create_standard_network, configure, ProviderConfig
from agents import Runner


# Estrategia: modelo mais barato que atende a necessidade de cada agente
AGENT_PROVIDERS = {
    # TIER 1 — Nano/Flash: tarefas de classificacao simples
    # Custo: ~$0.10/M input tokens
    "triage":   ProviderConfig(provider="openai", model="gpt-4.1-nano"),
    "feedback": ProviderConfig(provider="openai", model="gpt-4.1-nano"),
    "usage":    ProviderConfig(provider="gemini", model="gemini-2.0-flash"),

    # TIER 2 — Mini: tarefas que exigem algum raciocinio
    # Custo: ~$0.40/M input tokens
    "flow":         ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "interview":    ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "confirmation": ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "onboarding":   ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
    "escalation":   ProviderConfig(provider="openai", model="gpt-4.1-mini"),

    # TIER 3 — Pro: respostas ao usuario final (qualidade importa)
    # Custo: ~$1.10/M input tokens (DeepSeek muito mais barato que OpenAI/Claude)
    "knowledge": ProviderConfig(provider="deepseek", model="deepseek-chat"),
    "answer":    ProviderConfig(provider="deepseek", model="deepseek-chat"),
}

# Resumo de custo por tier:
#
# | Tier   | Agentes                              | Modelo          | $/M input |
# |--------|--------------------------------------|-----------------|-----------|
# | Nano   | triage, feedback, usage              | gpt-4.1-nano    | ~$0.10    |
# | Mini   | flow, interview, confirm, escalation | gpt-4.1-mini    | ~$0.40    |
# | Pro    | knowledge, answer                    | deepseek-chat   | ~$0.27    |


async def main():
    configure(provider="openai", default_model="gpt-4.1-nano")

    templates_root = Path(__file__).parent.parent / "client_templates"

    print("Criando rede otimizada para custo...\n")
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        agent_providers=AGENT_PROVIDERS,
    )

    print("Rede criada!\n")
    print(f"  {'Agente':<16} {'Provider':<12} {'Modelo':<24} {'Tier'}")
    print(f"  {'-'*16} {'-'*12} {'-'*24} {'-'*8}")
    tiers = {
        "gpt-4.1-nano": "Nano", "gemini-2.0-flash": "Flash",
        "gpt-4.1-mini": "Mini", "deepseek-chat": "Pro",
    }
    for name, pc in AGENT_PROVIDERS.items():
        tier = tiers.get(pc.model, "?")
        print(f"  {name:<16} {pc.provider:<12} {pc.model:<24} {tier}")

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
    print("=" * 56)
    print("  AtendentePro - Cost-Optimized Multi-Provider")
    print("  ~77% economia vs modelo unico")
    print("=" * 56)
    asyncio.run(main())
