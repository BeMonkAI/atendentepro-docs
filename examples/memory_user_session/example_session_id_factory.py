# -*- coding: utf-8 -*-
"""
Exemplo: session_id via network.session_id_factory.

Quando session_id não é passado e não vem do UserContext, run_with_memory
usa network.session_id_factory(network, messages) para obter o ID da sessão.
Útil para derivar sessão por canal, conversa ou hash das mensagens.
"""

import asyncio
import hashlib
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


def session_by_conversation_hash(network, messages):
    """
    Gera um session_id estável por conversa (hash das últimas N mensagens e user_id).
    Incluir user_id no hash evita colisão de session_id entre usuários: a mesma
    "conversa" recente do mesmo usuário usa a mesma sessão; usuários diferentes não colidem.
    """
    user_id = None
    if getattr(network, "loaded_user_context", None):
        user_id = getattr(network.loaded_user_context, "user_id", None)
    last_n = 6
    recent = messages[-last_n:] if len(messages) >= last_n else messages
    h = hashlib.sha256((str(user_id or "") + str(recent)).encode()).hexdigest()[:16]
    return f"sess_{h}"


async def main():
    setup_env()

    templates_root = Path(__file__).parent.parent.parent.parent / "templates"
    backend = MockMemoryBackend()

    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
    )
    network.memory_backend = backend

    # Definir factory na rede: session_id derivado das mensagens
    network.session_id_factory = session_by_conversation_hash

    print("\n" + "=" * 60)
    print("session_id_factory: uma sessão por hash da conversa")
    print("=" * 60)

    # Conversa A
    messages_a = [{"role": "user", "content": "Qual o horário de funcionamento?"}]
    result_a = await run_with_memory(
        network, network.triage, messages_a,
        user_id="user_web",
    )
    print(f"\n[Conversa A] Resposta: {result_a.final_output[:150]}...")

    # Mesma conversa A (mesmas mensagens → mesmo hash → mesma sessão)
    messages_a2 = messages_a + [
        {"role": "assistant", "content": result_a.final_output},
        {"role": "user", "content": "E aos sábados?"},
    ]
    result_a2 = await run_with_memory(
        network, network.triage, messages_a2,
        user_id="user_web",
    )
    print(f"\n[Conversa A - 2º turno] Resposta: {result_a2.final_output[:150]}...")

    # Conversa B (mensagens diferentes → outro hash → outra sessão)
    messages_b = [{"role": "user", "content": "Preço do plano premium?"}]
    await run_with_memory(
        network, network.triage, messages_b,
        user_id="user_web",
    )
    print("\n[Conversa B] Turno salvo em outra sessão (hash diferente).")

    print("\nChaves (user_id, session_id) no backend:")
    for key in backend.get_stored_keys():
        print(f"  {key}")

    # Canal compartilhado é o caso comum: um número/canal (WhatsApp, e-mail, Teams)
    # para vários clientes. session_id = canal; user_id = cliente/contato.
    # Sempre passar user_id para isolar memórias por cliente.
    print("\n" + "=" * 60)
    print("session_id_factory simulando canal (ex.: request)")
    print("=" * 60)

    channel_id = "whatsapp_5511999999999"

    def session_from_channel(network, messages):
        return channel_id

    network.session_id_factory = session_from_channel
    network.memory_backend = MockMemoryBackend()

    msg = [{"role": "user", "content": "Olá pelo WhatsApp."}]
    await run_with_memory(network, network.triage, msg, user_id="user_wa")
    print(f"\nSession ID usado: {channel_id}")
    print("Chaves:", network.memory_backend.get_stored_keys())

    print("\n✅ Exemplo concluído.")


if __name__ == "__main__":
    asyncio.run(main())
