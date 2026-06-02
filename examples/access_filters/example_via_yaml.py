# -*- coding: utf-8 -*-
"""
Exemplo: Configurando Filtros de Acesso via YAML.

Este exemplo mostra como carregar configurações de acesso
a partir do arquivo access_config.yaml.
"""

import asyncio
from pathlib import Path

from atendentepro import (
    activate,
    create_standard_network,
    UserContext,
)
from atendentepro.templates import load_access_config


async def exemplo_carregando_yaml():
    """
    Carregar configuração de acesso do arquivo YAML.
    
    O arquivo access_config.yaml permite configurar filtros
    sem modificar código Python.
    """
    print("\n" + "=" * 60)
    print("Exemplo: Carregando Filtros de Acesso via YAML")
    print("=" * 60)
    
    templates_root = Path(__file__).parent
    
    # Carregar e exibir configuração
    try:
        config = load_access_config()
    except FileNotFoundError:
        print("⚠️ access_config.yaml não encontrado, usando configuração padrão")
        config = None
    
    if config:
        print(f"\n📄 Arquivo: {templates_root}/access_config.yaml")
        
        print(f"\n🔒 Filtros de Agente:")
        for agent, filter_cfg in config.agent_filters.items():
            print(f"   - {agent}:")
            if filter_cfg.allowed_roles:
                print(f"     allowed_roles: {filter_cfg.allowed_roles}")
            if filter_cfg.denied_roles:
                print(f"     denied_roles: {filter_cfg.denied_roles}")
        
        print(f"\n📝 Prompts Condicionais:")
        for agent, prompts in config.conditional_prompts.items():
            print(f"   - {agent}: {len(prompts)} seções condicionais")
        
        print(f"\n🔧 Acesso a Tools:")
        for tool, filter_cfg in config.tool_access.items():
            roles = filter_cfg.allowed_roles or ["todos"]
            print(f"   - {tool}: {roles}")
    
    # Criar network para diferentes usuários
    print("\n" + "-" * 40)
    print("Testando com diferentes roles:")
    print("-" * 40)
    
    for role in ["admin", "vendedor", "cliente"]:
        user = UserContext(user_id=f"user_{role}", role=role)
        
        # Criar network (carrega access_config.yaml automaticamente)
        network = create_standard_network(
            templates_root=templates_root,
            client="config",
            user_context=user,
        )
        
        agent_names = [a.name for a in network.get_all_agents()]
        print(f"\n👤 Role: {role}")
        print(f"   Agentes: {len(agent_names)}")
        
        # Verificar agentes específicos
        has_feedback = network.feedback is not None
        has_escalation = network.escalation is not None
        print(f"   Feedback: {'✅' if has_feedback else '❌'}")
        print(f"   Escalation: {'✅' if has_escalation else '❌'}")


async def exemplo_yaml_com_override():
    """
    Carregar YAML mas sobrescrever algumas configurações via código.
    """
    print("\n" + "=" * 60)
    print("Exemplo: YAML com Override via Código")
    print("=" * 60)
    
    from atendentepro import AccessFilter, FilteredPromptSection
    
    templates_root = Path(__file__).parent
    
    # Usuário vendedor
    user = UserContext(user_id="vendedor_especial", role="vendedor")
    
    # Override: dar acesso ao feedback mesmo que YAML negue
    agent_filters_override = {
        "feedback": AccessFilter(
            allowed_users=["vendedor_especial"],  # Este vendedor específico pode
        ),
    }
    
    # Override: adicionar prompt extra
    conditional_prompts_override = {
        "knowledge": [
            FilteredPromptSection(
                content="\n\n## Acesso Especial\nVocê é um vendedor com privilégios especiais.",
                filter=AccessFilter(allowed_users=["vendedor_especial"]),
            ),
        ],
    }
    
    network = create_standard_network(
        templates_root=templates_root,
        client="config",
        user_context=user,
        agent_filters=agent_filters_override,
        conditional_prompts=conditional_prompts_override,
    )
    
    print(f"\n✅ Network criada com YAML + override")
    print(f"👤 Usuário: vendedor_especial (role=vendedor)")
    print(f"🔓 Feedback Agent incluído: {network.feedback is not None}")
    print(f"   (Override deu acesso especial a este vendedor)")


async def main():
    """Executar exemplos."""
    print("🔐 Exemplos de Filtros de Acesso via YAML")
    print("=" * 60)
    
    await exemplo_carregando_yaml()
    await exemplo_yaml_com_override()
    
    print("\n" + "=" * 60)
    print("✅ Exemplos concluídos!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
