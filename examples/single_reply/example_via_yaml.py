# -*- coding: utf-8 -*-
"""
Exemplo: Configurando Single Reply Mode via YAML.

Este exemplo mostra como carregar configurações de single_reply
a partir do arquivo single_reply_config.yaml.
"""

import asyncio
from pathlib import Path

from atendentepro import activate, create_standard_network
from atendentepro.templates import load_single_reply_config


async def exemplo_carregando_yaml():
    """
    Carregar configuração de single_reply do arquivo YAML.
    
    O arquivo single_reply_config.yaml permite configurar o comportamento
    sem modificar código Python.
    """
    print("\n" + "=" * 60)
    print("Exemplo: Carregando Single Reply via YAML")
    print("=" * 60)
    
    # Caminho para a pasta com os arquivos de configuração
    templates_root = Path(__file__).parent
    
    # Carregar e exibir configuração
    config = load_single_reply_config(templates_root)
    
    print(f"\n📄 Arquivo: {templates_root}/single_reply_config.yaml")
    print(f"🌍 Global: {config.global_single_reply}")
    print(f"👥 Agentes configurados:")
    
    if config.agents:
        for agent, enabled in config.agents.__dict__.items():
            if enabled is not None:
                status = "✅ single_reply" if enabled else "❌ múltiplas interações"
                print(f"   - {agent}: {status}")
    
    # Criar network (automaticamente carrega single_reply_config.yaml)
    network = create_standard_network(
        templates_root=templates_root,
        client="config",
        # Não precisa especificar single_reply_agents aqui
        # A configuração é carregada automaticamente do YAML
    )
    
    print("\n✅ Network criada com configurações do YAML")
    
    return network


async def exemplo_yaml_com_override():
    """
    Carregar YAML mas sobrescrever algumas configurações via código.
    
    Útil quando você quer usar YAML como base mas ajustar
    dinamicamente em runtime.
    """
    print("\n" + "=" * 60)
    print("Exemplo: YAML com Override via Código")
    print("=" * 60)
    
    templates_root = Path(__file__).parent
    
    # Carregar configuração base do YAML
    config = load_single_reply_config(templates_root)
    
    # Converter para dicionário e modificar
    agents_config = {}
    if config.agents:
        for agent in ['flow', 'interview', 'answer', 'knowledge', 
                      'confirmation', 'usage', 'escalation', 'feedback', 'onboarding']:
            value = getattr(config.agents, agent, None)
            if value is not None:
                agents_config[agent] = value
    
    # Override: forçar interview para True em um cenário específico
    agents_config["interview"] = True  # Override!
    
    print(f"\n📄 Base do YAML, mas interview sobrescrito para True")
    
    network = create_standard_network(
        templates_root=templates_root,
        client="config",
        global_single_reply=config.global_single_reply,
        single_reply_agents=agents_config,  # Usa config modificada
    )
    
    print("✅ Network criada com YAML + override")
    
    return network


async def main():
    """Executar exemplos."""
    print("🔁 Exemplos de Single Reply via YAML")
    print("=" * 60)
    
    await exemplo_carregando_yaml()
    await exemplo_yaml_com_override()
    
    print("\n" + "=" * 60)
    print("✅ Exemplos concluídos!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
