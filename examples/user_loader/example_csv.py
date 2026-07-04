# -*- coding: utf-8 -*-
"""
Exemplo: Carregamento de Usuários a partir de CSV.

Este exemplo mostra como usar o User Loader para carregar dados de usuários
de um arquivo CSV e identificar automaticamente usuários nas conversas.
"""

import asyncio
import os
import sys
from pathlib import Path

# Adicionar path para importar atendentepro
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from atendentepro import (
    activate,
    create_standard_network,
    create_user_loader,
    load_user_from_csv,
    extract_email_from_messages,
    extract_phone_from_messages,
    run_with_user_context,
)
from agents import set_default_openai_client, set_default_openai_api
from openai import AsyncOpenAI


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

# Ativar licença
license_key = os.getenv("ATENDENTEPRO_LICENSE_KEY")
if not license_key:
    print("❌ ATENDENTEPRO_LICENSE_KEY não configurada!")
    sys.exit(1)

try:
    activate(license_key)
except Exception as e:
    print(f"❌ Erro ao ativar licença: {e}")
    sys.exit(1)

# Configurar OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY não configurada!")
    sys.exit(1)

client = AsyncOpenAI(api_key=api_key)
set_default_openai_client(client)
set_default_openai_api("chat_completions")


# =============================================================================
# LOADER DE CSV
# =============================================================================

def load_user_from_csv_file(identifier: str):
    """
    Carrega usuário do CSV usando email ou telefone.
    
    Args:
        identifier: Email ou telefone do usuário
        
    Returns:
        Dict com dados do usuário ou None se não encontrado
    """
    csv_path = Path(__file__).parent / "users.csv"
    
    # Tentar buscar por email primeiro
    user_data = load_user_from_csv(
        csv_path=csv_path,
        identifier_field="email",
        identifier_value=identifier,
    )
    
    # Se não encontrou, tentar por telefone
    if not user_data:
        user_data = load_user_from_csv(
            csv_path=csv_path,
            identifier_field="telefone",
            identifier_value=identifier,
        )
    
    return user_data


# Criar loader que tenta email primeiro, depois telefone
def create_csv_loader():
    """Cria loader que tenta extrair email ou telefone."""
    def extract_identifier(messages):
        # Tenta email primeiro
        email = extract_email_from_messages(messages)
        if email:
            return email
        
        # Se não encontrou email, tenta telefone
        phone = extract_phone_from_messages(messages)
        if phone:
            return phone
        
        return None
    
    return create_user_loader(
        loader_func=load_user_from_csv_file,
        identifier_extractor=extract_identifier,
    )


# =============================================================================
# EXEMPLO
# =============================================================================

async def exemplo_usuario_existente():
    """Exemplo com usuário que existe no CSV."""
    print("\n" + "=" * 60)
    print("Exemplo 1: Usuário Existente (joao@example.com)")
    print("=" * 60)
    
    # Criar loader
    loader = create_csv_loader()
    
    # Criar network com loader
    templates_root = Path(__file__).parent.parent.parent.parent / "templates"
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        user_loader=loader,
        include_onboarding=True,
    )
    
    # Mensagem do usuário com email
    messages = [
        {"role": "user", "content": "Olá, meu email é joao@example.com"}
    ]
    
    print("\n📥 Carregando usuário...")
    result = await run_with_user_context(network, network.triage, messages)
    
    # Verificar se usuário foi carregado
    if network.loaded_user_context:
        print(f"\n✅ Usuário carregado:")
        print(f"   - ID: {network.loaded_user_context.user_id}")
        print(f"   - Role: {network.loaded_user_context.role}")
        print(f"   - Nome: {network.loaded_user_context.metadata.get('nome', 'N/A')}")
        print(f"   - Plano: {network.loaded_user_context.metadata.get('plano', 'N/A')}")
    else:
        print("\n❌ Usuário não encontrado")
    
    print(f"\n🤖 Resposta: {result.final_output}")


async def exemplo_usuario_nao_existente():
    """Exemplo com usuário que NÃO existe no CSV."""
    print("\n" + "=" * 60)
    print("Exemplo 2: Usuário NÃO Existente (novo@example.com)")
    print("=" * 60)
    
    # Criar loader
    loader = create_csv_loader()
    
    # Criar network com loader
    templates_root = Path(__file__).parent.parent.parent.parent / "templates"
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        user_loader=loader,
        include_onboarding=True,
    )
    
    # Mensagem do usuário com email que não existe
    messages = [
        {"role": "user", "content": "Olá, meu email é novo@example.com"}
    ]
    
    print("\n📥 Tentando carregar usuário...")
    result = await run_with_user_context(network, network.triage, messages)
    
    # Verificar se usuário foi carregado
    if network.loaded_user_context:
        print(f"\n✅ Usuário carregado: {network.loaded_user_context.user_id}")
    else:
        print("\n❌ Usuário não encontrado - será direcionado para onboarding")
    
    print(f"\n🤖 Resposta: {result.final_output}")


async def exemplo_telefone():
    """Exemplo usando telefone como identificador."""
    print("\n" + "=" * 60)
    print("Exemplo 3: Identificação por Telefone")
    print("=" * 60)
    
    # Criar loader
    loader = create_csv_loader()
    
    # Criar network com loader
    templates_root = Path(__file__).parent.parent.parent.parent / "templates"
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        user_loader=loader,
        include_onboarding=True,
    )
    
    # Mensagem do usuário com telefone
    messages = [
        {"role": "user", "content": "Meu telefone é (11) 99999-8888"}
    ]
    
    print("\n📥 Carregando usuário por telefone...")
    result = await run_with_user_context(network, network.triage, messages)
    
    # Verificar se usuário foi carregado
    if network.loaded_user_context:
        print(f"\n✅ Usuário carregado:")
        print(f"   - ID: {network.loaded_user_context.user_id}")
        print(f"   - Nome: {network.loaded_user_context.metadata.get('nome', 'N/A')}")
    else:
        print("\n❌ Usuário não encontrado")
    
    print(f"\n🤖 Resposta: {result.final_output}")


async def main():
    """Executa todos os exemplos."""
    print("=" * 60)
    print("  User Loader - Exemplo com CSV")
    print("=" * 60)
    
    await exemplo_usuario_existente()
    await exemplo_usuario_nao_existente()
    await exemplo_telefone()
    
    print("\n" + "=" * 60)
    print("✅ Exemplos concluídos!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
