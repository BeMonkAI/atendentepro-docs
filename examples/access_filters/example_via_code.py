# -*- coding: utf-8 -*-
"""
Exemplo: Configurando Filtros de Acesso via código Python.

Este exemplo mostra como configurar filtros de acesso baseados em
role e user diretamente no código, sem usar arquivos YAML.
"""

import asyncio
from pathlib import Path

from atendentepro import (
    activate,
    create_standard_network,
    UserContext,
    AccessFilter,
    FilteredPromptSection,
    FilteredTool,
)
from agents import function_tool


# =============================================================================
# TOOLS DE EXEMPLO (com filtros)
# =============================================================================

@function_tool
def consultar_comissao(vendedor_id: str) -> str:
    """Consulta comissões de um vendedor."""
    return f"Comissões do vendedor {vendedor_id}: R$ 1.500,00"


@function_tool
def aprovar_desconto(pedido_id: str, percentual: float) -> str:
    """Aprova desconto especial para um pedido."""
    return f"Desconto de {percentual}% aprovado para pedido {pedido_id}"


@function_tool
def deletar_cliente(cliente_id: str) -> str:
    """Remove um cliente do sistema (operação admin)."""
    return f"Cliente {cliente_id} removido do sistema"


# =============================================================================
# EXEMPLOS
# =============================================================================

async def exemplo_vendedor():
    """
    Exemplo 1: Rede configurada para um vendedor.
    
    O vendedor:
    - Tem acesso a Knowledge, Interview, Answer
    - NÃO tem acesso a Feedback (só admin)
    - Vê instruções específicas de desconto (até 15%)
    - Pode usar tool de consultar_comissao
    """
    print("\n" + "=" * 60)
    print("Exemplo 1: Usuário com role='vendedor'")
    print("=" * 60)
    
    # Contexto do usuário (normalmente vem da autenticação)
    user = UserContext(
        user_id="vendedor_123",
        role="vendedor",
        metadata={"department": "sales", "region": "sudeste"}
    )
    
    # Filtros de agente
    agent_filters = {
        "feedback": AccessFilter(allowed_roles=["admin"]),  # Só admin
        "escalation": AccessFilter(denied_roles=["cliente"]),  # Todos exceto cliente
    }
    
    # Prompts condicionais
    conditional_prompts = {
        "knowledge": [
            FilteredPromptSection(
                content="\n\n## Capacidades de Vendedor\nVocê pode oferecer até 15% de desconto e parcelamento em 12x.",
                filter=AccessFilter(allowed_roles=["vendedor"]),
            ),
            FilteredPromptSection(
                content="\n\n## Capacidades de Admin\nVocê tem acesso total ao sistema.",
                filter=AccessFilter(allowed_roles=["admin"]),
            ),
        ],
    }
    
    # Tools filtradas
    filtered_tools = {
        "knowledge": [
            FilteredTool(
                tool=consultar_comissao,
                filter=AccessFilter(allowed_roles=["vendedor", "gerente", "admin"]),
            ),
            FilteredTool(
                tool=aprovar_desconto,
                filter=AccessFilter(allowed_roles=["gerente", "admin"]),  # Vendedor NÃO pode
            ),
        ],
    }
    
    network = create_standard_network(
        templates_root=Path(__file__).parent,
        client="config",
        user_context=user,
        agent_filters=agent_filters,
        conditional_prompts=conditional_prompts,
        filtered_tools=filtered_tools,
    )
    
    print(f"\n✅ Network criada para vendedor")
    print(f"📋 Agentes disponíveis:")
    for agent in network.get_all_agents():
        print(f"   - {agent.name}")
    
    # Verificar se feedback está incluído (não deveria)
    print(f"\n🔒 Feedback Agent incluído: {network.feedback is not None}")
    print(f"🔒 Escalation Agent incluído: {network.escalation is not None}")
    
    return network


async def exemplo_admin():
    """
    Exemplo 2: Rede configurada para um administrador.
    
    O admin:
    - Tem acesso a TODOS os agentes
    - Vê instruções específicas de admin
    - Pode usar TODAS as tools
    """
    print("\n" + "=" * 60)
    print("Exemplo 2: Usuário com role='admin'")
    print("=" * 60)
    
    user = UserContext(
        user_id="admin_001",
        role="admin",
    )
    
    # Mesmos filtros - mas admin passa em todos
    agent_filters = {
        "feedback": AccessFilter(allowed_roles=["admin"]),
    }
    
    conditional_prompts = {
        "knowledge": [
            FilteredPromptSection(
                content="\n\n## Painel Administrativo\nVocê tem acesso a relatórios, métricas e configurações do sistema.",
                filter=AccessFilter(allowed_roles=["admin"]),
            ),
        ],
    }
    
    filtered_tools = {
        "knowledge": [
            FilteredTool(
                tool=deletar_cliente,
                filter=AccessFilter(allowed_roles=["admin"]),
            ),
        ],
    }
    
    network = create_standard_network(
        templates_root=Path(__file__).parent,
        client="config",
        user_context=user,
        agent_filters=agent_filters,
        conditional_prompts=conditional_prompts,
        filtered_tools=filtered_tools,
    )
    
    print(f"\n✅ Network criada para admin")
    print(f"📋 Agentes disponíveis:")
    for agent in network.get_all_agents():
        print(f"   - {agent.name}")
    
    print(f"\n🔓 Feedback Agent incluído: {network.feedback is not None}")
    
    return network


async def exemplo_cliente():
    """
    Exemplo 3: Rede configurada para um cliente.
    
    O cliente:
    - Tem acesso limitado (sem escalation direta)
    - Vê apenas informações públicas
    - Não pode usar tools administrativas
    """
    print("\n" + "=" * 60)
    print("Exemplo 3: Usuário com role='cliente'")
    print("=" * 60)
    
    user = UserContext(
        user_id="cliente_456",
        role="cliente",
    )
    
    agent_filters = {
        "escalation": AccessFilter(denied_roles=["cliente"]),  # Cliente não pode escalar
        "feedback": AccessFilter(allowed_roles=["admin"]),
    }
    
    conditional_prompts = {
        "knowledge": [
            FilteredPromptSection(
                content="\n\n## Informações para Cliente\nVocê pode consultar produtos, preços e status de pedidos.",
                filter=AccessFilter(allowed_roles=["cliente"]),
            ),
        ],
    }
    
    network = create_standard_network(
        templates_root=Path(__file__).parent,
        client="config",
        user_context=user,
        agent_filters=agent_filters,
        conditional_prompts=conditional_prompts,
    )
    
    print(f"\n✅ Network criada para cliente")
    print(f"📋 Agentes disponíveis:")
    for agent in network.get_all_agents():
        print(f"   - {agent.name}")
    
    print(f"\n🔒 Escalation Agent incluído: {network.escalation is not None}")
    
    return network


async def exemplo_usuario_especifico():
    """
    Exemplo 4: Filtro por usuário específico.
    
    Permite dar acesso especial a usuários específicos,
    independente da role.
    """
    print("\n" + "=" * 60)
    print("Exemplo 4: Filtro por usuário específico")
    print("=" * 60)
    
    # Usuário VIP que tem acesso especial mesmo sendo cliente
    user = UserContext(
        user_id="cliente_vip_001",
        role="cliente",
    )
    
    agent_filters = {
        "escalation": AccessFilter(
            denied_roles=["cliente"],
            allowed_users=["cliente_vip_001"],  # Este cliente VIP pode escalar!
        ),
    }
    
    network = create_standard_network(
        templates_root=Path(__file__).parent,
        client="config",
        user_context=user,
        agent_filters=agent_filters,
    )
    
    print(f"\n✅ Network criada para cliente VIP")
    print(f"🔓 Escalation Agent incluído: {network.escalation is not None}")
    print(f"   (Cliente VIP tem permissão especial para escalar)")
    
    return network


async def main():
    """Executar todos os exemplos."""
    print("🔐 Exemplos de Filtros de Acesso")
    print("=" * 60)
    
    await exemplo_vendedor()
    await exemplo_admin()
    await exemplo_cliente()
    await exemplo_usuario_especifico()
    
    print("\n" + "=" * 60)
    print("✅ Todos os exemplos executados com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
