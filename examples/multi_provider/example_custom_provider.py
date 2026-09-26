# -*- coding: utf-8 -*-
"""
Exemplo: Provider customizado (Ollama, vLLM, etc.)

Quando o provider não está em KNOWN_PROVIDERS, passe base_url
e api_key explicitamente no ProviderConfig.

Funciona com qualquer API compatível OpenAI:
  - Ollama (local)
  - vLLM (self-hosted)
  - Together AI
  - Groq
  - OpenRouter
  - Fireworks AI

.env:
    ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
    OPENAI_API_KEY=sk-...  (fallback)
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from atendentepro import activate, configure, create_standard_network, ProviderConfig
from agents import Runner

activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))
configure(provider="openai", default_model="gpt-4.1-mini")

AGENT_PROVIDERS = {
    # Ollama local — sem custo, privacidade total
    "triage": ProviderConfig(
        provider="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # Ollama aceita qualquer string
    ),
    "flow": ProviderConfig(
        provider="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    ),

    # vLLM self-hosted — modelo grande, GPU dedicada
    "knowledge": ProviderConfig(
        provider="vllm",
        model="mistralai/Mistral-Large-Instruct-2407",
        base_url="http://gpu-server:8000/v1",
        api_key="token-interno",
    ),
    "answer": ProviderConfig(
        provider="vllm",
        model="mistralai/Mistral-Large-Instruct-2407",
        base_url="http://gpu-server:8000/v1",
        api_key="token-interno",
    ),

    # Together AI — modelos open-source na nuvem
    "interview": ProviderConfig(
        provider="together",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        base_url="https://api.together.xyz/v1",
        api_key=os.getenv("TOGETHER_API_KEY", ""),
    ),

    # Groq — inferência ultra-rápida
    "confirmation": ProviderConfig(
        provider="groq",
        model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY", ""),
    ),
}


async def main():
    network = create_standard_network(
        templates_root=Path("./config"),
        client="meu_cliente",
        agent_providers=AGENT_PROVIDERS,
    )

    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Como funciona a instalação?"}],
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
