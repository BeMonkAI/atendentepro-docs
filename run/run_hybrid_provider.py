#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro — Hibrido (agent_providers + agent_models)

Demonstra como combinar os dois mecanismos:
  - agent_providers: agentes criticos com provider dedicado (Model instance)
  - agent_models: demais agentes usando o provider global com modelo especifico

Agentes em agent_providers tem prioridade sobre agent_models.
Agentes que nao aparecem em nenhum usam o default_model global.

Requer:
    OPENAI_API_KEY=sk-...     (provider global + triage/flow)
    DEEPSEEK_API_KEY=sk-...   (knowledge/answer via ProviderConfig)
"""

import asyncio
from pathlib import Path

from atendentepro import create_standard_network, configure, ProviderConfig
from agents import Runner


# Apenas os agentes criticos usam provider dedicado
AGENT_PROVIDERS = {
    "knowledge": ProviderConfig(provider="deepseek", model="deepseek-reasoner"),
    "answer":    ProviderConfig(provider="deepseek", model="deepseek-chat"),
}

# Demais agentes usam o provider global (OpenAI) com modelo especifico
AGENT_MODELS = {
    "triage":       "gpt-4.1-mini",
    "flow":         "gpt-4.1-mini",
    "interview":    "gpt-4.1-mini",
    "confirmation": "gpt-4.1-mini",
    "escalation":   "gpt-4.1-mini",
    "feedback":     "gpt-4.1-nano",
    "usage":        "gpt-4.1-nano",
}

# Resolucao:
# 1. knowledge/answer -> agent_providers (DeepSeek, Model instance)
# 2. triage/flow/etc  -> agent_models (OpenAI, string)
# 3. onboarding       -> nenhum dos dois -> default_model (gpt-4.1-mini)


async def main():
    # Provider global: OpenAI (usado por agent_models e como fallback)
    configure(provider="openai", default_model="gpt-4.1-mini")

    templates_root = Path(__file__).parent.parent / "client_templates"

    print("Criando rede hibrida (OpenAI + DeepSeek)...\n")
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        agent_providers=AGENT_PROVIDERS,
        agent_models=AGENT_MODELS,
    )

    # Mostrar resolucao
    all_agents = [
        "triage", "flow", "interview", "answer", "knowledge",
        "confirmation", "usage", "escalation", "feedback",
    ]
    print("Rede criada!\n")
    print(f"  {'Agente':<16} {'Origem':<18} {'Provider':<12} {'Modelo'}")
    print(f"  {'-'*16} {'-'*18} {'-'*12} {'-'*24}")
    for name in all_agents:
        if name in AGENT_PROVIDERS:
            pc = AGENT_PROVIDERS[name]
            print(f"  {name:<16} {'agent_providers':<18} {pc.provider:<12} {pc.model}")
        elif name in AGENT_MODELS:
            print(f"  {name:<16} {'agent_models':<18} {'openai':<12} {AGENT_MODELS[name]}")
        else:
            print(f"  {name:<16} {'default_model':<18} {'openai':<12} gpt-4.1-mini")

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
    print("  AtendentePro - Hybrid Provider (OpenAI + DeepSeek)")
    print("=" * 56)
    asyncio.run(main())
