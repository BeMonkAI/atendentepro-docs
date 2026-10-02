# -*- coding: utf-8 -*-
"""
Exemplo: user_loader apenas com dados do cliente; session_id por factory ou parâmetro.

O user_loader deve retornar apenas dados do usuário que vêm de banco/cadastro
(user_id, role, metadata de perfil ou estatísticas). Não use para memória ou
session_id — esses vêm de session_id_factory ou parâmetro. O user_loader retorna
UserContext(user_id, role, metadata); session_id vem de network.session_id_factory
ou do parâmetro de run_with_memory.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from atendentepro import activate, create_standard_network
from atendentepro.models import UserContext
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


def make_user_loader(user_id: str, role: str = "cliente"):
    """
    user_loader retorna só dados do usuário de banco/cadastro (user_id, role, metadata).
    Em produção, você extrairia isso do request/cadastro (ex.: JWT, DB).
    Importante: retornar o user_id do request atual — não reutilizar contexto de outro
    usuário, senão a memória pode ser associada à pessoa errada.
    Não use para memória ou session_id — sessão vem de session_id_factory ou parâmetro.
    """

    def loader(messages):
        return UserContext(
            user_id=user_id,
            role=role,
            metadata={"plano": "premium", "canal": "web"},
        )

    return loader


async def main():
    setup_env()

    templates_root = Path(__file__).parent.parent.parent.parent / "templates"
    backend = MockMemoryBackend()

    # user_loader: apenas dados do cliente
    user_id = "usr_julia"
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        user_loader=make_user_loader(user_id),
    )
    network.memory_backend = backend

    # session_id: da rede (session_id_factory), ex.: ID da conversa no request
    conversation_id = "conversa_123"
    network.session_id_factory = lambda n, msgs: conversation_id

    print("\n" + "=" * 60)
    print("user_loader só com user_id/role/metadata; session_id via session_id_factory")
    print("=" * 60)
    print(f"\nuser_loader retorna: user_id={user_id}, role=cliente, metadata (plano, canal)")
    print(f"session_id vem de network.session_id_factory: {conversation_id}\n")

    # Primeira mensagem: user_id do context, session_id da factory
    messages1 = [{"role": "user", "content": "Quero cadastrar meu cartão."}]
    result1 = await run_with_memory(network, network.triage, messages1)
    print(f"Resposta 1: {result1.final_output[:180]}...")

    # Segunda mensagem: mesma sessão (factory retorna mesmo ID), memória da primeira
    messages2 = [
        {"role": "user", "content": "Quero cadastrar meu cartão."},
        {"role": "assistant", "content": result1.final_output},
        {"role": "user", "content": "O que eu acabei de pedir?"},
    ]
    result2 = await run_with_memory(network, network.triage, messages2)
    print(f"\nResposta 2 (com memória): {result2.final_output[:180]}...")

    print("\n→ user_id de network.loaded_user_context (user_loader); session_id de session_id_factory.")
    print("  Chaves no backend:", backend.get_stored_keys())

    # Alternativa: session_id por parâmetro em vez de factory
    print("\n" + "=" * 60)
    print("session_id por parâmetro (em vez de factory)")
    print("=" * 60)

    network2 = create_standard_network(
        templates_root=templates_root,
        client="standard",
        user_loader=make_user_loader("usr_marco"),
    )
    network2.memory_backend = MockMemoryBackend()

    msg = [{"role": "user", "content": "Teste com session_id no parâmetro."}]
    await run_with_memory(
        network2, network2.triage, msg,
        session_id="sess_param_demo",
    )
    print("Turno salvo com user_id=usr_marco (user_loader), session_id=sess_param_demo (parâmetro).")

    print("\n✅ Exemplo concluído.")


if __name__ == "__main__":
    asyncio.run(main())
