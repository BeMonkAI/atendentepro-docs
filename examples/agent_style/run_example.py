# -*- coding: utf-8 -*-
"""
Exemplo Interativo: AgentStyle

Permite testar diferentes estilos de comunicação em uma conversa real.

Uso:
    python run_example.py
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

try:
    from agents import Runner
except ImportError:
    print("❌ Instale o openai-agents: pip install openai-agents")
    exit(1)


# =============================================================================
# Estilos Predefinidos
# =============================================================================

STYLES = {
    "1": {
        "name": "🏛️ Formal",
        "description": "Profissional e respeitoso (bancos, governo)",
        "global": AgentStyle(
            tone="profissional e respeitoso",
            language_style="formal",
            response_length="moderado",
        ),
        "agents": {},
    },
    "2": {
        "name": "😊 Amigável",
        "description": "Descontraído e próximo (startups, apps)",
        "global": AgentStyle(
            tone="amigável e descontraído",
            language_style="informal",
            response_length="conciso",
        ),
        "agents": {},
    },
    "3": {
        "name": "🔧 Técnico",
        "description": "Preciso e detalhado (suporte técnico)",
        "global": AgentStyle(
            tone="técnico e preciso",
            language_style="neutro",
            response_length="detalhado",
        ),
        "agents": {
            "knowledge": AgentStyle(
                tone="didático e técnico",
                response_length="detalhado",
            ),
        },
    },
    "4": {
        "name": "💚 Empático",
        "description": "Acolhedor e compreensivo (SAC, reclamações)",
        "global": AgentStyle(
            tone="empático e acolhedor",
            language_style="formal",
            response_length="moderado",
        ),
        "agents": {
            "escalation": AgentStyle(
                tone="muito empático e tranquilizador",
                custom_rules="Demonstre máxima compreensão.",
            ),
        },
    },
    "5": {
        "name": "⚡ Conciso",
        "description": "Direto ao ponto (chatbots rápidos)",
        "global": AgentStyle(
            tone="objetivo e eficiente",
            language_style="neutro",
            response_length="conciso",
            custom_rules="Respostas curtas e diretas. Máximo 2 frases quando possível.",
        ),
        "agents": {},
    },
}


def select_style() -> dict:
    """Permite ao usuário selecionar um estilo."""
    print("\n" + "=" * 50)
    print("🎨 Selecione um Estilo de Comunicação:")
    print("=" * 50 + "\n")
    
    for key, style in STYLES.items():
        print(f"  [{key}] {style['name']}")
        print(f"      {style['description']}\n")
    
    print("  [0] Sem estilo (padrão)")
    print()
    
    choice = input("Escolha (1-5, ou 0): ").strip()
    
    if choice in STYLES:
        return STYLES[choice]
    
    return None


async def run_conversation(network, style_name: str):
    """Executa uma conversa interativa."""
    
    print("\n" + "=" * 50)
    print(f"💬 Conversa com estilo: {style_name}")
    print("=" * 50)
    print("(Digite 'sair' para encerrar)\n")
    
    messages = []
    
    while True:
        try:
            user_input = input("Você: ").strip()
        except EOFError:
            break
        
        if user_input.lower() in ["sair", "exit", "quit", "q"]:
            print("\n👋 Até logo!")
            break
        
        if not user_input:
            continue
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            result = await Runner.run(network.triage, messages)
            response = str(result.final_output)
            print(f"\n🤖 Assistente: {response}\n")
            messages.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")


async def main():
    """Função principal."""
    
    print("\n" + "=" * 60)
    print("🎨 AtendentePro - Demo AgentStyle")
    print("=" * 60)
    
    # Verificar ativação
    if not is_activated():
        print("\n⚠️  AtendentePro não está ativado!")
        print("Configure ATENDENTEPRO_LICENSE_KEY no arquivo .env")
        print("\nExemplo de .env:")
        print("  ATENDENTEPRO_LICENSE_KEY=ATP_seu-token")
        print("  OPENAI_API_KEY=sk-sua-chave")
        return
    
    print("\n✅ AtendentePro ativado!")
    
    # Selecionar estilo
    style = select_style()
    
    # Criar rede
    print("\n⏳ Criando rede de agentes...")
    
    templates_path = Path(__file__).parent.parent.parent.parent / "templates"
    
    if style:
        network = create_standard_network(
            templates_root=templates_path,
            client="standard",
            global_style=style["global"],
            agent_styles=style["agents"],
            include_onboarding=False,
        )
        style_name = style["name"]
    else:
        network = create_standard_network(
            templates_root=templates_path,
            client="standard",
            include_onboarding=False,
        )
        style_name = "Padrão (sem estilo)"
    
    print("✅ Rede criada!")
    
    # Executar conversa
    await run_conversation(network, style_name)


if __name__ == "__main__":
    asyncio.run(main())
