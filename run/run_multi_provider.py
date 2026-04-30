#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo: AtendentePro com 4 provedores no mesmo sistema (nativo)

Usa OpenAI, DeepSeek, Gemini e Claude simultaneamente, cada agente
com o modelo mais adequado ao seu papel. Nao requer proxy externo —
usa o suporte nativo agent_providers do AtendentePro.

Variaveis de ambiente necessarias (.env):
    OPENAI_API_KEY=sk-...
    DEEPSEEK_API_KEY=sk-...
    GEMINI_API_KEY=...
    ANTHROPIC_API_KEY=sk-ant-...
"""

import asyncio
from pathlib import Path

from atendentepro import create_standard_network, configure, ProviderConfig
from agents import Runner


# Cada agente usa o provedor mais adequado ao seu papel.
# ProviderConfig resolve base_url e api_key automaticamente
# para provedores conhecidos (openai, deepseek, gemini, anthropic).
AGENT_PROVIDERS = {
    # --- OpenAI: triage e flow (roteamento rapido, baixa latencia) ---
    "triage": ProviderConfig(provider="openai", model="gpt-4.1-mini"),
    "flow":   ProviderConfig(provider="openai", model="gpt-4.1-mini"),

    # --- DeepSeek: knowledge e answer (raciocinio profundo, custo baixo) ---
    "knowledge": ProviderConfig(provider="deepseek", model="deepseek-reasoner"),
    "answer":    ProviderConfig(provider="deepseek", model="deepseek-chat"),

    # --- Gemini: interview e onboarding (contexto longo, multimodal) ---
    "interview":  ProviderConfig(provider="gemini", model="gemini-2.5-pro"),
    "onboarding": ProviderConfig(provider="gemini", model="gemini-2.0-flash"),

    # --- Claude: confirmation e escalation (instrucoes complexas, seguranca) ---
    "confirmation": ProviderConfig(provider="anthropic", model="claude-sonnet-4-6-20250514"),
    "escalation":   ProviderConfig(provider="anthropic", model="claude-sonnet-4-6-20250514"),

    # --- Modelos leves para tarefas simples ---
    "feedback": ProviderConfig(provider="openai", model="gpt-4.1-nano"),
    "usage":    ProviderConfig(provider="gemini", model="gemini-2.0-flash"),
}

# Justificativa da escolha de cada provedor:
#
# | Provedor   | Agentes              | Motivo                                    |
# |------------|----------------------|-------------------------------------------|
# | OpenAI     | triage, flow         | Latencia baixa, bom em classificacao      |
# | DeepSeek   | knowledge, answer    | Raciocinio chain-of-thought, custo baixo  |
# | Gemini     | interview, onboarding| Contexto longo (1M tokens), multimodal    |
# | Claude     | confirmation, escal. | Segue instrucoes complexas, safety forte  |


async def main():
    # Configurar provider padrao (fallback para agentes sem provider especifico)
    configure(provider="openai", default_model="gpt-4.1-mini")

    templates_root = Path(__file__).parent.parent / "client_templates"

    print("Criando rede multi-provider (nativo, sem proxy)...\n")

    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        agent_providers=AGENT_PROVIDERS,
    )

    # Mostrar configuracao
    print("Rede criada!\n")
    print(f"  {'Agente':<16} {'Provedor':<12} {'Modelo'}")
    print(f"  {'-'*16} {'-'*12} {'-'*36}")
    for name, pc in AGENT_PROVIDERS.items():
        print(f"  {name:<16} {pc.provider:<12} {pc.model}")

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
    print("  AtendentePro - Multi-Provider Nativo (4 LLMs)")
    print("  OpenAI + DeepSeek + Gemini + Claude")
    print("=" * 56)
    asyncio.run(main())
