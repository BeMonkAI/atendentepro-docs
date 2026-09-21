# -*- coding: utf-8 -*-
"""
Exemplo: AgentStyle via YAML

Demonstra como configurar o tom e estilo de comunicação dos agentes
usando um arquivo style_config.yaml.

Uso:
    python example_via_yaml.py
"""

import asyncio
from pathlib import Path

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

from atendentepro import (
    activate,
    create_standard_network,
    AgentStyle,
    is_activated,
)
from atendentepro.templates import load_style_config


def load_style_from_yaml() -> tuple:
    """
    Carrega configuração de estilo do arquivo YAML.
    
    Returns:
        Tuple com (global_style, agent_styles)
    """
    # Caminho para o style_config.yaml deste exemplo
    yaml_path = Path(__file__).parent / "style_config.yaml"
    
    if not yaml_path.exists():
        print(f"⚠️  Arquivo não encontrado: {yaml_path}")
        return None, None
    
    # Carregar configuração
    # Nota: load_style_config usa o TemplateManager, então precisamos
    # configurar manualmente aqui para este exemplo standalone
    
    import yaml
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    # Criar AgentStyle global
    global_data = data.get("global", {})
    global_style = AgentStyle(
        tone=global_data.get("tone", ""),
        language_style=global_data.get("language_style", ""),
        response_length=global_data.get("response_length", ""),
        custom_rules=global_data.get("custom_rules", ""),
    )
    
    # Criar AgentStyles por agente
    agent_styles = {}
    for agent_name, agent_data in data.get("agents", {}).items():
        agent_styles[agent_name] = AgentStyle(
            tone=agent_data.get("tone", ""),
            language_style=agent_data.get("language_style", ""),
            response_length=agent_data.get("response_length", ""),
            custom_rules=agent_data.get("custom_rules", ""),
        )
    
    return global_style, agent_styles


def create_network_from_yaml():
    """
    Cria uma rede de agentes usando configuração do YAML.
    """
    global_style, agent_styles = load_style_from_yaml()
    
    if global_style is None:
        print("❌ Não foi possível carregar o style_config.yaml")
        return None
    
    return create_standard_network(
        templates_root=Path(__file__).parent.parent.parent.parent / "templates",
        client="standard",
        global_style=global_style,
        agent_styles=agent_styles,
        include_onboarding=False,
    )


async def demo_yaml_style():
    """Demonstra carregamento de estilos via YAML."""
    
    print("=" * 60)
    print("📄 DEMO: AgentStyle via YAML")
    print("=" * 60)
    
    # Verificar ativação
    if not is_activated():
        print("\n⚠️  AtendentePro não está ativado!")
        print("Configure ATENDENTEPRO_LICENSE_KEY no .env")
        return
    
    print("\n✅ AtendentePro ativado!\n")
    
    # Carregar estilos do YAML
    print("📂 Carregando style_config.yaml...\n")
    
    global_style, agent_styles = load_style_from_yaml()
    
    if global_style is None:
        return
    
    # Mostrar configuração carregada
    print("🌐 Estilo Global:")
    print(f"   • Tom: {global_style.tone}")
    print(f"   • Linguagem: {global_style.language_style}")
    print(f"   • Respostas: {global_style.response_length}")
    
    print(f"\n🤖 Estilos por Agente ({len(agent_styles)} configurados):")
    for agent_name, style in agent_styles.items():
        print(f"\n   [{agent_name}]")
        if style.tone:
            print(f"   • Tom: {style.tone}")
        if style.language_style:
            print(f"   • Linguagem: {style.language_style}")
        if style.response_length:
            print(f"   • Respostas: {style.response_length}")
    
    print("\n" + "-" * 60)
    print("\n📝 Conteúdo do style_config.yaml:\n")
    
    yaml_path = Path(__file__).parent / "style_config.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        # Mostrar apenas as primeiras 30 linhas
        lines = f.readlines()[:30]
        for line in lines:
            print(f"   {line.rstrip()}")
        if len(lines) >= 30:
            print("   ...")
    
    print("\n" + "-" * 60)
    print("\n💡 Como usar em seu projeto:")
    print("""
1. Copie style_config.yaml para a pasta do seu cliente
2. Customize os valores conforme necessário
3. A rede carregará automaticamente:

   network = create_standard_network(
       templates_root=Path("./meu_cliente"),
       client="config",
   )
   
   # O style_config.yaml será carregado automaticamente
   # se existir na pasta do cliente
    """)
    
    print("-" * 60)
    print("\n✅ Para testar interativamente, execute: python run_example.py")


if __name__ == "__main__":
    asyncio.run(demo_yaml_style())
