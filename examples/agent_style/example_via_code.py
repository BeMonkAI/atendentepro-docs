# -*- coding: utf-8 -*-
"""
Exemplo: AgentStyle via Código

Demonstra como configurar o tom e estilo de comunicação dos agentes
programaticamente usando a classe AgentStyle.

Uso:
    python example_via_code.py
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


def create_formal_network():
    """
    Cria uma rede com estilo FORMAL.
    Ideal para: bancos, escritórios de advocacia, governo.
    """
    global_style = AgentStyle(
        tone="profissional e respeitoso",
        language_style="formal",
        response_length="moderado",
        custom_rules="""
- Use sempre tratamento formal (senhor/senhora)
- Evite contrações e gírias
- Cite normas e regulamentos quando aplicável
- Mantenha tom institucional
        """.strip(),
    )
    
    return create_standard_network(
        templates_root=Path(__file__).parent.parent.parent.parent / "templates",
        client="standard",
        global_style=global_style,
        include_onboarding=False,
    )


def create_friendly_network():
    """
    Cria uma rede com estilo AMIGÁVEL.
    Ideal para: startups, e-commerce, apps.
    """
    global_style = AgentStyle(
        tone="amigável e descontraído",
        language_style="informal",
        response_length="conciso",
        custom_rules="""
- Use linguagem próxima e acessível
- Emojis são bem-vindos ocasionalmente
- Seja direto e prático
- Demonstre entusiasmo genuíno
        """.strip(),
    )
    
    # Escalation continua empático mesmo no estilo amigável
    escalation_style = AgentStyle(
        tone="empático e acolhedor",
        custom_rules="Demonstre compreensão. Use linguagem acolhedora.",
    )
    
    return create_standard_network(
        templates_root=Path(__file__).parent.parent.parent.parent / "templates",
        client="standard",
        global_style=global_style,
        agent_styles={
            "escalation": escalation_style,
        },
        include_onboarding=False,
    )


def create_technical_network():
    """
    Cria uma rede com estilo TÉCNICO.
    Ideal para: suporte técnico, documentação, desenvolvedores.
    """
    global_style = AgentStyle(
        tone="técnico e preciso",
        language_style="neutro",
        response_length="detalhado",
        custom_rules="""
- Use terminologia técnica quando apropriado
- Forneça detalhes técnicos relevantes
- Inclua exemplos de código quando útil
- Cite documentação oficial
        """.strip(),
    )
    
    # Knowledge é ainda mais detalhado
    knowledge_style = AgentStyle(
        tone="didático e técnico",
        response_length="detalhado",
        custom_rules="""
- Explique conceitos técnicos em profundidade
- Use exemplos práticos e código
- Cite fontes e documentação
        """.strip(),
    )
    
    return create_standard_network(
        templates_root=Path(__file__).parent.parent.parent.parent / "templates",
        client="standard",
        global_style=global_style,
        agent_styles={
            "knowledge": knowledge_style,
        },
        include_onboarding=False,
    )


def create_empathetic_network():
    """
    Cria uma rede com estilo EMPÁTICO.
    Ideal para: SAC, reclamações, suporte emocional.
    """
    global_style = AgentStyle(
        tone="empático e acolhedor",
        language_style="formal",
        response_length="moderado",
        custom_rules="""
- Sempre demonstre compreensão pela situação
- Valide os sentimentos do usuário
- Peça desculpas quando apropriado
- Foque na solução, não no problema
        """.strip(),
    )
    
    # Escalation é ainda mais empático
    escalation_style = AgentStyle(
        tone="muito empático e tranquilizador",
        custom_rules="""
- Demonstre máxima compreensão
- Assegure que o problema SERÁ resolvido
- Mantenha calma mesmo sob pressão
- Ofereça alternativas e próximos passos claros
        """.strip(),
    )
    
    # Feedback também precisa ser acolhedor
    feedback_style = AgentStyle(
        tone="solícito e atencioso",
        custom_rules="""
- Agradeça genuinamente pelo feedback
- Demonstre que a opinião é valorizada
- Confirme próximos passos claramente
        """.strip(),
    )
    
    return create_standard_network(
        templates_root=Path(__file__).parent.parent.parent.parent / "templates",
        client="standard",
        global_style=global_style,
        agent_styles={
            "escalation": escalation_style,
            "feedback": feedback_style,
        },
        include_onboarding=False,
    )


async def demo_styles():
    """Demonstra os diferentes estilos disponíveis."""
    
    print("=" * 60)
    print("🎨 DEMO: AgentStyle - Estilos de Comunicação")
    print("=" * 60)
    
    # Verificar ativação
    if not is_activated():
        print("\n⚠️  AtendentePro não está ativado!")
        print("Configure ATENDENTEPRO_LICENSE_KEY no .env")
        return
    
    print("\n✅ AtendentePro ativado!\n")
    
    # Criar diferentes redes
    styles = {
        "formal": ("🏛️ FORMAL", create_formal_network),
        "friendly": ("😊 AMIGÁVEL", create_friendly_network),
        "technical": ("🔧 TÉCNICO", create_technical_network),
        "empathetic": ("💚 EMPÁTICO", create_empathetic_network),
    }
    
    print("Estilos disponíveis:\n")
    for key, (label, _) in styles.items():
        print(f"  {label}")
    
    print("\n" + "-" * 60)
    print("\nExemplo de configuração (Estilo Empático):\n")
    
    # Mostrar exemplo de código
    print("""
from atendentepro import create_standard_network, AgentStyle

global_style = AgentStyle(
    tone="empático e acolhedor",
    language_style="formal",
    response_length="moderado",
    custom_rules="Sempre demonstre compreensão pela situação.",
)

network = create_standard_network(
    templates_root=Path("./templates"),
    client="standard",
    global_style=global_style,
    agent_styles={
        "escalation": AgentStyle(tone="muito empático"),
    },
)
    """)
    
    print("-" * 60)
    print("\n✅ Para testar interativamente, execute: python run_example.py")


if __name__ == "__main__":
    asyncio.run(demo_styles())
