# -*- coding: utf-8 -*-
"""
Exemplo: Carregamento de Usuários a partir de Banco de Dados.

Este exemplo mostra como usar o User Loader com um banco de dados simulado
(usando dicionário em memória, mas pode ser facilmente adaptado para SQLite,
PostgreSQL, MySQL, etc.).
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Adicionar path para importar atendentepro
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from atendentepro import (
    activate,
    create_standard_network,
    create_user_loader,
    extract_email_from_messages,
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
# BANCO DE DADOS SIMULADO
# =============================================================================

# Simulação de banco de dados em memória
# Em produção, substitua por conexão real (SQLite, PostgreSQL, etc.)
USERS_DB: Dict[str, Dict] = {
    "joao@example.com": {
        "user_id": "user_001",
        "email": "joao@example.com",
        "nome": "João Silva",
        "telefone": "11999998888",
        "role": "cliente",
        "plano": "premium",
        "empresa": "Acme Corp",
        "ultimo_acesso": "2024-01-15",
    },
    "maria@example.com": {
        "user_id": "user_002",
        "email": "maria@example.com",
        "nome": "Maria Santos",
        "telefone": "11988887777",
        "role": "cliente",
        "plano": "basic",
        "empresa": "Tech Solutions",
        "ultimo_acesso": "2024-01-14",
    },
    "admin@example.com": {
        "user_id": "admin_001",
        "email": "admin@example.com",
        "nome": "Admin User",
        "telefone": "11977776666",
        "role": "admin",
        "plano": "enterprise",
        "empresa": "Internal",
        "ultimo_acesso": "2024-01-16",
    },
}


def load_user_from_database(identifier: str) -> Optional[Dict]:
    """
    Carrega usuário do banco de dados.
    
    Em produção, substitua por:
    - SQLite: sqlite3.connect("users.db")
    - PostgreSQL: psycopg2.connect(...)
    - MySQL: mysql.connector.connect(...)
    - MongoDB: pymongo.MongoClient(...)
    
    Args:
        identifier: Email do usuário
        
    Returns:
        Dict com dados do usuário ou None se não encontrado
    """
    # Simulação de query no banco
    # Em produção: cursor.execute("SELECT * FROM users WHERE email = ?", (identifier,))
    user = USERS_DB.get(identifier.lower())
    
    if user:
        return user
    
    return None


# Exemplo com SQLite (comentado para referência)
"""
import sqlite3

def load_user_from_database(identifier: str) -> Optional[Dict]:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT user_id, email, nome, telefone, role, plano, empresa "
        "FROM users WHERE email = ?",
        (identifier,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "email": row[1],
            "nome": row[2],
            "telefone": row[3],
            "role": row[4],
            "plano": row[5],
            "empresa": row[6],
        }
    
    return None
"""


# =============================================================================
# LOADER
# =============================================================================

loader = create_user_loader(
    loader_func=load_user_from_database,
    identifier_extractor=extract_email_from_messages,
)


# =============================================================================
# EXEMPLO
# =============================================================================

async def exemplo_com_banco():
    """Exemplo usando banco de dados."""
    print("\n" + "=" * 60)
    print("  User Loader - Exemplo com Banco de Dados")
    print("=" * 60)
    
    # Criar network com loader
    templates_root = Path(__file__).parent.parent.parent.parent / "templates"
    network = create_standard_network(
        templates_root=templates_root,
        client="standard",
        user_loader=loader,
        include_onboarding=True,
    )
    
    # Testar com diferentes usuários
    test_cases = [
        {
            "name": "Usuário Premium",
            "message": "Olá, meu email é joao@example.com",
        },
        {
            "name": "Usuário Admin",
            "message": "Meu email é admin@example.com",
        },
        {
            "name": "Usuário Não Existente",
            "message": "Meu email é novo@example.com",
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Teste {i}: {test_case['name']}")
        print("=" * 60)
        
        messages = [{"role": "user", "content": test_case["message"]}]
        
        print(f"\n📥 Mensagem: {test_case['message']}")
        print("📥 Carregando usuário...")
        
        result = await run_with_user_context(network, network.triage, messages)
        
        # Verificar se usuário foi carregado
        if network.loaded_user_context:
            print(f"\n✅ Usuário carregado do banco:")
            print(f"   - ID: {network.loaded_user_context.user_id}")
            print(f"   - Role: {network.loaded_user_context.role}")
            print(f"   - Nome: {network.loaded_user_context.metadata.get('nome', 'N/A')}")
            print(f"   - Plano: {network.loaded_user_context.metadata.get('plano', 'N/A')}")
            print(f"   - Empresa: {network.loaded_user_context.metadata.get('empresa', 'N/A')}")
        else:
            print("\n❌ Usuário não encontrado no banco")
        
        print(f"\n🤖 Resposta: {result.final_output[:200]}..." if len(str(result.final_output)) > 200 else f"\n🤖 Resposta: {result.final_output}")


async def main():
    """Executa o exemplo."""
    await exemplo_com_banco()
    
    print("\n" + "=" * 60)
    print("✅ Exemplo concluído!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
