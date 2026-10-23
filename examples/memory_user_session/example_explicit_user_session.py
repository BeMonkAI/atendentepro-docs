# -*- coding: utf-8 -*-
"""
Exemplo: user_id e session_id explícitos em run_with_memory.

Mostra como passar user_id e session_id diretamente em cada chamada
para isolar memórias por usuário e por sessão/conversa.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from atendentepro import activate, create_standard_network
from atendentepro.memory import run_with_memory
from agents import set_default_openai_client, set_default_openai_api
from openai import AsyncOpenAI

from mock_memory_backend import MockMemoryBackend


def setup_env():
    """Ativa licença e configura OpenAI."""
    license_key = os.getenv("ATENDENTEPRO_LICENSE_KEY")
    if not license_key:
        print("❌ ATENDENTEPRO_LICENSE_KEY não configurada!")
        sys.exit(1)
    activate(license_key)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY não configurada!")
        sys.exit(1)
    client = AsyncOpenAI(api_key=api_key)
    set_default_openai_client(client)
    set_default_openai_api("chat_completions")


async def main():
    setup_env()

    templates_root = Path(__file__).parent.parent.parent.parent / "templates"
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
    )

    # Backend de memória em memória (para exemplo; em produção use create_grk_backend())
    backend = MockMemoryBackend()
    network.memory_backend = backend

    print("\n" + "=" * 60)
    print("Exemplo 1: Um usuário, duas sessões (conversas diferentes)")
    print("=" * 60)

    # Sessão A: usuário user_123 conversando no canal WhatsApp
    messages_a1 = [{"role": "user", "content": "Quero saber o preço do plano básico."}]
    result_a = await run_with_memory(
        network, network.triage, messages_a1,
        user_id="user_123",
        session_id="sess_whatsapp_abc",
    )
    print(f"\n[user_123, sess_whatsapp_abc] Resposta: {result_a.final_output[:200]}...")

    # Sessão B: mesmo usuário, outra conversa (ex.: outro canal)
    messages_b1 = [{"role": "user", "content": "O que combinamos na última vez?"}]
    result_b = await run_with_memory(
        network, network.triage, messages_b1,
        user_id="user_123",
        session_id="sess_web_xyz",
    )
    print(f"\n[user_123, sess_web_xyz] Resposta: {result_b.final_output[:200]}...")
    print("\n→ Memórias ficam separadas por session_id (sess_whatsapp_abc vs sess_web_xyz).")

    print("\n" + "=" * 60)
    print("Exemplo 2: Dois usuários, memórias isoladas por user_id")
    print("=" * 60)
    # Passar user_id (e session_id quando aplicável) em toda chamada evita que
    # memórias de um usuário apareçam para outro (isolamento por chave user_id/session_id).

    # Usuário 1
    messages_u1 = [{"role": "user", "content": "Meu nome é Ana, quero contratar."}]
    await run_with_memory(
        network, network.triage, messages_u1,
        user_id="user_ana",
        session_id="sess_1",
    )
    print("\n[user_ana] Turno salvo.")

    # Usuário 2
    messages_u2 = [{"role": "user", "content": "O que a Ana combinou?"}]
    result_u2 = await run_with_memory(
        network, network.triage, messages_u2,
        user_id="user_bruno",
        session_id="sess_1",
    )
    print(f"\n[user_bruno] Resposta: {result_u2.final_output[:200]}...")
    print("→ user_bruno não vê as memórias de user_ana (isolamento por user_id).")

    print("\n" + "=" * 60)
    print("Chaves armazenadas no mock (user_id, session_id):")
    print("=" * 60)
    for key in backend.get_stored_keys():
        print(f"  {key}")

    print("\n✅ Exemplo concluído.")


if __name__ == "__main__":
    asyncio.run(main())
