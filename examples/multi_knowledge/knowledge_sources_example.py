# -*- coding: utf-8 -*-
"""
Exemplo de Knowledge Agent com Múltiplas Fontes de Dados

Este exemplo demonstra como criar um Knowledge Agent que integra:
1. 📄 Documentos (RAG com embeddings)
2. 📊 Tabelas (CSV, Excel)
3. 🗄️ Banco de Dados (SQLite/PostgreSQL)
4. 🌐 APIs Externas

Arquitetura:
┌─────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE AGENT                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  📄 RAG     │  │  📊 CSV     │  │  🗄️ SQL    │  │  🌐 API     │ │
│  │  Documents  │  │  Tables     │  │  Database   │  │  External   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │                │        │
│         └────────────────┴────────────────┴────────────────┘        │
│                                   │                                 │
│                            ┌──────▼──────┐                          │
│                            │   RESPOSTA  │                          │
│                            │   UNIFICADA │                          │
│                            └─────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
"""

import os
import csv
import json
import sqlite3
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, Field

from agents import Agent, function_tool

from atendentepro import activate
from atendentepro.agents import create_knowledge_agent, KnowledgeAgent
from atendentepro.models import ContextNote


# =============================================================================
# 1. FERRAMENTAS PARA CONSULTA DE TABELAS (CSV/Excel)
# =============================================================================

class CSVQueryInput(BaseModel):
    """Input para consulta em CSV."""
    query: str = Field(description="Termo de busca ou filtro")
    columns: Optional[List[str]] = Field(default=None, description="Colunas para retornar")


# Configuração global do path do CSV
_CSV_PATH: Optional[Path] = None
_CSV_DATA: List[Dict] = []


def configure_csv_source(csv_path: Path) -> None:
    """Configura o caminho do arquivo CSV."""
    global _CSV_PATH, _CSV_DATA
    _CSV_PATH = csv_path
    
    # Pré-carregar dados
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            _CSV_DATA = list(reader)


@function_tool
async def consultar_tabela_csv(query: str, max_results: int = 10) -> str:
    """
    Consulta dados em uma tabela CSV.
    
    Use para buscar informações em planilhas e tabelas de dados estruturados.
    Exemplos: lista de produtos, preços, estoque, clientes, pedidos.
    
    Args:
        query: Termo de busca (busca em todas as colunas)
        max_results: Número máximo de resultados
        
    Returns:
        Dados encontrados formatados como texto
    """
    if not _CSV_DATA:
        return "❌ Nenhuma tabela CSV configurada ou arquivo vazio."
    
    query_lower = query.lower()
    results = []
    
    for row in _CSV_DATA:
        # Busca em todos os valores do registro
        row_text = ' '.join(str(v).lower() for v in row.values())
        if query_lower in row_text:
            results.append(row)
            if len(results) >= max_results:
                break
    
    if not results:
        return f"🔍 Nenhum resultado encontrado para '{query}' na tabela."
    
    # Formatar resultado
    output = f"📊 Encontrados {len(results)} resultado(s) para '{query}':\n\n"
    for i, row in enumerate(results, 1):
        output += f"**Registro {i}:**\n"
        for key, value in row.items():
            output += f"  - {key}: {value}\n"
        output += "\n"
    
    return output


@function_tool
async def listar_colunas_csv() -> str:
    """
    Lista as colunas disponíveis na tabela CSV.
    
    Use para descobrir quais campos/colunas estão disponíveis para consulta.
    
    Returns:
        Lista de colunas da tabela
    """
    if not _CSV_DATA:
        return "❌ Nenhuma tabela CSV configurada."
    
    columns = list(_CSV_DATA[0].keys()) if _CSV_DATA else []
    total_rows = len(_CSV_DATA)
    
    return f"📊 Tabela com {total_rows} registros\n\nColunas disponíveis:\n" + \
           "\n".join(f"  - {col}" for col in columns)


# =============================================================================
# 2. FERRAMENTAS PARA CONSULTA DE BANCO DE DADOS (SQL)
# =============================================================================

_DB_CONNECTION: Optional[sqlite3.Connection] = None

_ALLOWED_TABLES = {"clientes", "pedidos"}
_ALLOWED_COLUMNS = {
    "id", "nome", "email", "cidade", "data_cadastro",
    "cliente_id", "produto", "valor", "status", "data_pedido",
}


def configure_database(db_path: Path) -> None:
    """Configura a conexão com o banco de dados SQLite."""
    global _DB_CONNECTION
    _DB_CONNECTION = sqlite3.connect(str(db_path))
    _DB_CONNECTION.row_factory = sqlite3.Row


@function_tool
async def consultar_banco_dados(
    tabela: str,
    colunas: Optional[str] = None,
    campo_filtro: Optional[str] = None,
    valor_filtro: Optional[str] = None,
    limite: int = 10
) -> str:
    """
    Consulta dados em um banco de dados SQL com queries parametrizadas.
    
    Use para buscar informações em tabelas de banco de dados.
    Exemplos: histórico de pedidos, cadastros, transações.
    
    Args:
        tabela: Nome da tabela a consultar (clientes ou pedidos)
        colunas: Colunas a retornar separadas por vírgula (ex: "nome, email")
        campo_filtro: Nome da coluna para filtrar (ex: "status")
        valor_filtro: Valor a buscar no campo de filtro (ex: "ativo")
        limite: Número máximo de resultados
        
    Returns:
        Dados encontrados formatados
    """
    if not _DB_CONNECTION:
        return "❌ Banco de dados não configurado."
    
    if tabela not in _ALLOWED_TABLES:
        return f"❌ Tabela '{tabela}' não permitida. Tabelas disponíveis: {', '.join(sorted(_ALLOWED_TABLES))}"
    
    try:
        if colunas and colunas != "*":
            cols_list = [c.strip() for c in colunas.split(",")]
            if not all(c in _ALLOWED_COLUMNS for c in cols_list):
                invalid = [c for c in cols_list if c not in _ALLOWED_COLUMNS]
                return f"❌ Coluna(s) não permitida(s): {', '.join(invalid)}"
            cols = ", ".join(cols_list)
        else:
            cols = "*"
        
        query = f"SELECT {cols} FROM {tabela}"
        params: list[object] = []
        
        if campo_filtro and valor_filtro:
            if campo_filtro not in _ALLOWED_COLUMNS:
                return f"❌ Campo de filtro '{campo_filtro}' não permitido."
            query += f" WHERE {campo_filtro} = ?"
            params.append(valor_filtro)
        
        query += " LIMIT ?"
        params.append(limite)
        
        cursor = _DB_CONNECTION.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return f"🔍 Nenhum resultado encontrado na tabela '{tabela}'."
        
        columns = [description[0] for description in cursor.description]
        output = f"🗄️ Encontrados {len(rows)} resultado(s) em '{tabela}':\n\n"
        
        for i, row in enumerate(rows, 1):
            output += f"**Registro {i}:**\n"
            for col, val in zip(columns, row):
                output += f"  - {col}: {val}\n"
            output += "\n"
        
        return output
        
    except Exception:
        return "❌ Erro ao consultar banco de dados."


@function_tool
async def listar_tabelas_banco() -> str:
    """
    Lista as tabelas disponíveis no banco de dados.
    
    Use para descobrir quais tabelas estão disponíveis para consulta.
    
    Returns:
        Lista de tabelas do banco
    """
    if not _DB_CONNECTION:
        return "❌ Banco de dados não configurado."
    
    try:
        cursor = _DB_CONNECTION.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            return "📭 Banco de dados vazio (nenhuma tabela)."
        
        output = "🗄️ Tabelas disponíveis:\n\n"
        for table in tables:
            if table not in _ALLOWED_TABLES:
                continue
            count = _DB_CONNECTION.execute(
                "SELECT COUNT(*) FROM " + table, []
            ).fetchone()[0]
            output += f"  - **{table}** ({count} registros)\n"
        
        return output
        
    except Exception:
        return "❌ Erro ao listar tabelas."


# =============================================================================
# 3. FERRAMENTAS PARA CONSULTA DE APIs EXTERNAS
# =============================================================================

@dataclass
class APIConfig:
    """Configuração de uma API externa."""
    name: str
    base_url: str
    headers: Dict[str, str] = None
    description: str = ""


_API_CONFIGS: Dict[str, APIConfig] = {}


def configure_api(name: str, base_url: str, headers: Dict[str, str] = None, description: str = "") -> None:
    """Registra uma API externa para consulta."""
    _API_CONFIGS[name] = APIConfig(
        name=name,
        base_url=base_url,
        headers=headers or {},
        description=description
    )


@function_tool
async def consultar_api_externa(
    api_name: str,
    endpoint: str,
    params: Optional[str] = None
) -> str:
    """
    Consulta uma API externa registrada.
    
    Use para buscar informações em tempo real de sistemas externos.
    Exemplos: cotações, status de serviços, dados de terceiros.
    
    Args:
        api_name: Nome da API registrada
        endpoint: Endpoint a consultar (ex: "/produtos/123")
        params: Parâmetros de query string em JSON (ex: '{"status": "ativo"}')
        
    Returns:
        Resposta da API formatada
    """
    if api_name not in _API_CONFIGS:
        available = ", ".join(_API_CONFIGS.keys()) if _API_CONFIGS else "nenhuma"
        return f"❌ API '{api_name}' não encontrada. Disponíveis: {available}"
    
    config = _API_CONFIGS[api_name]
    url = f"{config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    try:
        query_params = json.loads(params) if params else None
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=config.headers,
                params=query_params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
        
        # Formatar resposta
        output = f"🌐 Resposta da API '{api_name}' ({endpoint}):\n\n"
        output += json.dumps(data, indent=2, ensure_ascii=False)
        
        return output
        
    except httpx.HTTPError:
        return "❌ Erro HTTP ao consultar API."
    except json.JSONDecodeError:
        return "❌ Resposta da API não é JSON válido."
    except Exception:
        return "❌ Erro ao consultar API."


@function_tool
async def listar_apis_disponiveis() -> str:
    """
    Lista as APIs externas disponíveis para consulta.
    
    Returns:
        Lista de APIs configuradas
    """
    if not _API_CONFIGS:
        return "📭 Nenhuma API externa configurada."
    
    output = "🌐 APIs disponíveis:\n\n"
    for name, config in _API_CONFIGS.items():
        output += f"  - **{name}**\n"
        output += f"    URL: {config.base_url}\n"
        if config.description:
            output += f"    Descrição: {config.description}\n"
        output += "\n"
    
    return output


# =============================================================================
# 4. CRIAR O KNOWLEDGE AGENT COMPLETO
# =============================================================================

def create_knowledge_agent_multi_source(
    name: str = "Knowledge Agent Multi-Source",
    # Fontes de dados
    embeddings_path: Optional[Path] = None,  # RAG/Documentos
    csv_path: Optional[Path] = None,          # Tabelas CSV
    db_path: Optional[Path] = None,           # Banco SQLite
    apis: Optional[List[Dict]] = None,        # APIs externas
    # Configurações
    handoffs: Optional[List] = None,
    custom_instructions: Optional[str] = None,
) -> KnowledgeAgent:
    """
    Cria um Knowledge Agent com múltiplas fontes de dados.
    
    Args:
        name: Nome do agente
        embeddings_path: Path para embeddings de documentos (RAG)
        csv_path: Path para arquivo CSV
        db_path: Path para banco SQLite
        apis: Lista de configurações de APIs [{"name": "...", "base_url": "...", ...}]
        handoffs: Agentes para handoff
        custom_instructions: Instruções customizadas
        
    Returns:
        Knowledge Agent configurado
        
    Example:
        >>> agent = create_knowledge_agent_multi_source(
        ...     embeddings_path=Path("./docs_embeddings.pkl"),
        ...     csv_path=Path("./produtos.csv"),
        ...     db_path=Path("./database.db"),
        ...     apis=[{
        ...         "name": "cotacao",
        ...         "base_url": "https://api.cotacao.com",
        ...         "description": "API de cotações em tempo real"
        ...     }]
        ... )
    """
    
    # Configurar fontes de dados
    tools = []
    sources_description = []
    
    # 1. Configurar CSV
    if csv_path and csv_path.exists():
        configure_csv_source(csv_path)
        tools.extend([consultar_tabela_csv, listar_colunas_csv])
        sources_description.append(f"📊 Tabela CSV: {csv_path.name}")
    
    # 2. Configurar Banco de Dados
    if db_path and db_path.exists():
        configure_database(db_path)
        tools.extend([consultar_banco_dados, listar_tabelas_banco])
        sources_description.append(f"🗄️ Banco de dados: {db_path.name}")
    
    # 3. Configurar APIs
    if apis:
        for api_config in apis:
            configure_api(**api_config)
        tools.extend([consultar_api_externa, listar_apis_disponiveis])
        sources_description.append(f"🌐 APIs externas: {len(apis)} configuradas")
    
    # Descrição das fontes
    data_sources = "\n".join(sources_description) if sources_description else "Nenhuma fonte adicional configurada"
    
    # Criar agente base com RAG (se tiver embeddings)
    agent = create_knowledge_agent(
        name=name,
        knowledge_about=f"""
        Knowledge Agent com múltiplas fontes de dados:
        
        {data_sources}
        
        Capacidades:
        - Buscar em documentos via RAG (se configurado)
        - Consultar tabelas CSV
        - Consultar banco de dados SQL
        - Consultar APIs externas
        """,
        knowledge_template="Fonte: {tipo} | Consulta: {query}",
        knowledge_format="Responda consolidando informações de todas as fontes relevantes.",
        embeddings_path=embeddings_path,
        data_sources_description=data_sources,
        include_rag_tool=embeddings_path is not None and embeddings_path.exists(),
        tools=tools,
        handoffs=handoffs,
        custom_instructions=custom_instructions or f"""
        Você é um Knowledge Agent com acesso a MÚLTIPLAS fontes de dados.
        
        FONTES DISPONÍVEIS:
        {data_sources}
        
        ESTRATÉGIA DE BUSCA:
        1. Analise a pergunta do usuário
        2. Identifique qual(is) fonte(s) é mais adequada
        3. Use as ferramentas apropriadas para buscar dados
        4. Consolide as informações em uma resposta clara
        
        FERRAMENTAS DISPONÍVEIS:
        - go_to_rag: Buscar em documentos (manuais, políticas, etc.)
        - consultar_tabela_csv: Buscar em tabelas de dados
        - consultar_banco_dados: Buscar em banco SQL
        - consultar_api_externa: Buscar em APIs externas
        - listar_*: Descobrir estrutura das fontes
        
        IMPORTANTE:
        - Sempre cite a fonte dos dados
        - Se não encontrar em uma fonte, tente outras
        - Combine informações de múltiplas fontes quando relevante
        """,
    )
    
    return agent


# =============================================================================
# 5. EXEMPLO DE USO COMPLETO
# =============================================================================

async def main():
    """Exemplo de uso do Knowledge Agent Multi-Source."""
    
    # Ativar biblioteca
    # activate("ATP_seu-token-aqui")
    
    # Criar dados de exemplo
    example_dir = Path("./example_data")
    example_dir.mkdir(exist_ok=True)
    
    # 1. Criar CSV de exemplo
    csv_path = example_dir / "produtos.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'nome', 'categoria', 'preco', 'estoque'])
        writer.writeheader()
        writer.writerows([
            {'id': '1', 'nome': 'Notebook Pro', 'categoria': 'Eletrônicos', 'preco': '4500.00', 'estoque': '15'},
            {'id': '2', 'nome': 'Mouse Wireless', 'categoria': 'Periféricos', 'preco': '89.90', 'estoque': '150'},
            {'id': '3', 'nome': 'Teclado Mecânico', 'categoria': 'Periféricos', 'preco': '350.00', 'estoque': '45'},
            {'id': '4', 'nome': 'Monitor 27"', 'categoria': 'Eletrônicos', 'preco': '1800.00', 'estoque': '20'},
            {'id': '5', 'nome': 'Webcam HD', 'categoria': 'Periféricos', 'preco': '299.00', 'estoque': '80'},
        ])
    print(f"✅ CSV criado: {csv_path}")
    
    # 2. Criar banco de dados de exemplo
    db_path = example_dir / "vendas.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            email TEXT,
            cidade TEXT,
            data_cadastro TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY,
            cliente_id INTEGER,
            produto TEXT,
            valor REAL,
            status TEXT,
            data_pedido TEXT
        )
    ''')
    # Inserir dados de exemplo
    conn.executemany('INSERT OR REPLACE INTO clientes VALUES (?, ?, ?, ?, ?)', [
        (1, 'João Silva', 'joao@email.com', 'São Paulo', '2024-01-15'),
        (2, 'Maria Santos', 'maria@email.com', 'Rio de Janeiro', '2024-02-20'),
        (3, 'Pedro Costa', 'pedro@email.com', 'Belo Horizonte', '2024-03-10'),
    ])
    conn.executemany('INSERT OR REPLACE INTO pedidos VALUES (?, ?, ?, ?, ?, ?)', [
        (1, 1, 'Notebook Pro', 4500.00, 'entregue', '2024-06-01'),
        (2, 1, 'Mouse Wireless', 89.90, 'entregue', '2024-06-05'),
        (3, 2, 'Monitor 27"', 1800.00, 'enviado', '2024-06-10'),
        (4, 3, 'Teclado Mecânico', 350.00, 'processando', '2024-06-12'),
    ])
    conn.commit()
    conn.close()
    print(f"✅ Banco criado: {db_path}")
    
    # 3. Criar o Knowledge Agent
    agent = create_knowledge_agent_multi_source(
        name="Knowledge Agent E-Commerce",
        csv_path=csv_path,
        db_path=db_path,
        apis=[
            {
                "name": "viacep",
                "base_url": "https://viacep.com.br/ws",
                "description": "API de consulta de CEPs"
            }
        ]
    )
    
    print(f"\n✅ Knowledge Agent criado: {agent.name}")
    print("\n" + "="*60)
    print("FERRAMENTAS DISPONÍVEIS:")
    print("="*60)
    for tool in agent.tools:
        print(f"  - {tool.name}")
    
    # 4. Testar as ferramentas individualmente
    print("\n" + "="*60)
    print("TESTANDO FONTES DE DADOS:")
    print("="*60)
    
    # Testar CSV
    print("\n📊 CSV - Buscando 'mouse':")
    result = await consultar_tabela_csv("mouse")
    print(result)
    
    # Testar Banco
    print("\n🗄️ BANCO - Listando tabelas:")
    result = await listar_tabelas_banco()
    print(result)
    
    print("\n🗄️ BANCO - Consultando clientes:")
    result = await consultar_banco_dados("clientes")
    print(result)
    
    # Testar API
    print("\n🌐 API - Consultando CEP:")
    result = await consultar_api_externa("viacep", "01310100/json")
    print(result)
    
    print("\n" + "="*60)
    print("✅ Exemplo completo executado!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

