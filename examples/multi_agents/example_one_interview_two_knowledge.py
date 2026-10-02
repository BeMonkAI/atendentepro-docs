# -*- coding: utf-8 -*-
"""
Exemplo: 1 Interview → 2 Knowledge Agents

Este exemplo demonstra como criar uma rede onde:
- 1 Interview Agent coleta dados do usuário
- 2 Knowledge Agents respondem sobre domínios diferentes

Caso de uso: Suporte técnico que precisa consultar:
- Knowledge de Produtos (especificações, funcionalidades)
- Knowledge de Troubleshooting (problemas, soluções)
"""

import asyncio
from pathlib import Path

from atendentepro import (
    activate,
    create_custom_network,
    create_triage_agent,
    create_interview_agent,
    create_knowledge_agent,
    create_answer_agent,
    create_escalation_agent,
    AgentNetwork,
)


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

INTERVIEW_QUESTIONS = """
Para ajudá-lo com seu problema técnico, preciso de algumas informações:

1. **Qual produto você está usando?** (Ex: SmartTV X500, Soundbar Pro, etc.)
2. **Qual é o problema?** (Descreva o que está acontecendo)
3. **Quando começou?** (O problema é novo ou já acontecia antes?)
4. **O que você já tentou?** (Reiniciar, desligar, etc.)
"""

KNOWLEDGE_PRODUTOS = """
Você é especialista em **especificações de produtos**:

## SmartTV X500
- Tela: 55" 4K UHD
- Processador: Quad-Core
- HDR: Dolby Vision + HDR10
- Smart: Android TV 11
- Conexões: 3 HDMI, 2 USB, Wi-Fi 6
- Áudio: 20W, Dolby Atmos

## SmartTV X700
- Tela: 65" 8K QLED
- Processador: Octa-Core
- HDR: Dolby Vision IQ
- Smart: Android TV 12
- Conexões: 4 HDMI 2.1, 3 USB
- Áudio: 60W, harman/kardon

## Soundbar Pro
- Canais: 5.1.2
- Potência: 400W
- Conexões: HDMI eARC, Óptica, Bluetooth 5.0
- Subwoofer: Wireless incluso
- Compatível: Dolby Atmos, DTS:X

## Soundbar Basic
- Canais: 2.1
- Potência: 150W
- Conexões: HDMI ARC, Óptica, Bluetooth 4.2
- Subwoofer: Integrado
"""

KNOWLEDGE_TROUBLESHOOTING = """
Você é especialista em **troubleshooting e soluções técnicas**:

## SmartTV - Problemas Comuns

### TV não liga
1. Verificar se o cabo de energia está bem conectado
2. Testar em outra tomada
3. Segurar botão de power por 10 segundos
4. Se não resolver: possível problema na placa de energia

### Sem imagem mas com som
1. Verificar configuração de entrada (HDMI, TV, etc.)
2. Testar com outra entrada HDMI
3. Reiniciar a TV (desligar da tomada por 30s)
4. Reset de fábrica: Configurações > Sistema > Resetar

### Wi-Fi não conecta
1. Reiniciar roteador e TV
2. Esquecer rede e reconectar
3. Verificar distância do roteador
4. Atualizar firmware da TV

## Soundbar - Problemas Comuns

### Sem som
1. Verificar conexão HDMI/Óptica
2. Configurar saída de áudio da TV
3. Verificar se soundbar está no modo correto (HDMI, BT, etc.)
4. Reiniciar soundbar (desligar 10s)

### Bluetooth não pareia
1. Colocar soundbar em modo pairing (LED piscando)
2. Remover dispositivo antigo do celular
3. Aproximar celular da soundbar
4. Reiniciar Bluetooth do celular

### Subwoofer sem som
1. Verificar se LED do sub está aceso
2. Re-parear com soundbar (botão no sub por 5s)
3. Verificar configuração de volume do sub
"""

TRIAGE_KEYWORDS = """
## Direcionamento

### Para Interview (Coletar dados do problema)
- "problema", "não funciona", "ajuda", "suporte"
- "quebrou", "defeito", "erro", "bug"

### Para Knowledge Produtos (Especificações)
- "especificação", "ficha técnica", "quantos watts"
- "qual a diferença", "comparar", "recursos"

### Para Knowledge Troubleshooting (Soluções)
- "como resolver", "o que fazer", "solução"
- "não liga", "sem som", "não conecta"
"""


def create_one_interview_two_knowledge_network() -> AgentNetwork:
    """
    Cria uma rede com 1 Interview que pode direcionar para 2 Knowledge.
    
    Fluxo:
    
        Triage ─┬──> Interview ─┬──> Knowledge Produtos
                │               └──> Knowledge Troubleshooting
                ├──> Knowledge Produtos (consulta direta)
                └──> Knowledge Troubleshooting (consulta direta)
    """
    
    # 1. Triage Agent
    triage = create_triage_agent(
        keywords_text=TRIAGE_KEYWORDS,
        name="triage_agent",
    )
    
    # 2. Interview Agent (único, coleta dados do problema)
    interview = create_interview_agent(
        interview_template="Suporte Técnico",
        interview_questions=INTERVIEW_QUESTIONS,
        name="interview_agent",
    )
    
    # 3. Knowledge Agent - Produtos (especificações)
    knowledge_produtos = create_knowledge_agent(
        knowledge_about=KNOWLEDGE_PRODUTOS,
        knowledge_template="Especificações de Produtos",
        knowledge_format="Forneça informações técnicas claras e objetivas.",
        name="knowledge_produtos",
        single_reply=True,
    )
    
    # 4. Knowledge Agent - Troubleshooting (soluções)
    knowledge_troubleshooting = create_knowledge_agent(
        knowledge_about=KNOWLEDGE_TROUBLESHOOTING,
        knowledge_template="Soluções Técnicas",
        knowledge_format="Forneça passos claros e numerados para resolver o problema.",
        name="knowledge_troubleshooting",
        single_reply=True,
    )
    
    # 5. Answer Agent
    answer = create_answer_agent(
        answer_template="",
        name="answer_agent",
    )
    
    # 6. Escalation Agent
    escalation = create_escalation_agent(
        escalation_channels="Técnico disponível: segunda a sexta, 8h às 18h.",
        name="escalation_agent",
    )
    
    # =========================================================================
    # CONFIGURAR HANDOFFS
    # =========================================================================
    
    # Triage -> Interview ou Knowledge direto
    triage.handoffs = [
        interview,               # Coletar dados do problema
        knowledge_produtos,      # Consulta direta de specs
        knowledge_troubleshooting,  # Consulta direta de soluções
        escalation,              # Escalar para humano
    ]
    
    # Interview -> Pode ir para QUALQUER Knowledge
    interview.handoffs = [
        knowledge_produtos,         # Buscar specs do produto
        knowledge_troubleshooting,  # Buscar solução do problema
        answer,                     # Responder com base nos dados
        triage,                     # Voltar ao início
        escalation,                 # Escalar se necessário
    ]
    
    # Knowledge Produtos -> Volta ao Triage ou vai para Troubleshooting
    knowledge_produtos.handoffs = [
        triage,                     # Voltar ao início
        knowledge_troubleshooting,  # Se precisar de solução após specs
        escalation,
    ]
    
    # Knowledge Troubleshooting -> Volta ao Triage ou vai para Produtos
    knowledge_troubleshooting.handoffs = [
        triage,                     # Voltar ao início
        knowledge_produtos,         # Se precisar de specs após solução
        escalation,
    ]
    
    # Answer -> Triage
    answer.handoffs = [triage, escalation]
    
    # Escalation -> Triage
    escalation.handoffs = [triage]
    
    # =========================================================================
    # CRIAR NETWORK
    # =========================================================================
    
    network = create_custom_network(
        triage=triage,
        custom_agents={
            "interview": interview,
            "knowledge_produtos": knowledge_produtos,
            "knowledge_troubleshooting": knowledge_troubleshooting,
            "answer": answer,
            "escalation": escalation,
        },
    )
    
    return network


async def demonstrate_routing():
    """
    Demonstra os cenários de roteamento.
    """
    print("\n" + "=" * 60)
    print("🔀 Exemplo: 1 Interview → 2 Knowledge")
    print("=" * 60)
    
    network = create_one_interview_two_knowledge_network()
    
    # Listar agentes
    print("\n📋 Agentes na rede:")
    for agent in network.get_all_agents():
        handoff_names = [h.name for h in getattr(agent, 'handoffs', [])]
        print(f"   - {agent.name}")
        if handoff_names:
            print(f"     └─ handoffs: {', '.join(handoff_names)}")
    
    # Cenários
    print("\n" + "-" * 40)
    print("📌 Cenários de Roteamento:")
    print("-" * 40)
    
    scenarios = [
        # Fluxo completo via Interview
        (
            "Minha TV não está ligando",
            "Triage → Interview (coletar dados) → Knowledge Troubleshooting"
        ),
        (
            "Qual a potência da Soundbar Pro?",
            "Triage → Knowledge Produtos (direto)"
        ),
        (
            "Como resolver o Bluetooth que não conecta?",
            "Triage → Knowledge Troubleshooting (direto)"
        ),
        # Fluxo misto
        (
            "Preciso saber as specs e resolver problema",
            "Triage → Interview → Knowledge Produtos → Knowledge Troubleshooting"
        ),
    ]
    
    for mensagem, rota in scenarios:
        print(f"\n💬 '{mensagem}'")
        print(f"   → {rota}")
    
    # Diagrama
    print("\n" + "-" * 40)
    print("📊 Diagrama de Fluxo:")
    print("-" * 40)
    print("""
                    ┌───────────────┐
                    │    Triage     │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Interview   │   │   Knowledge   │   │   Knowledge   │
│ (coleta dados)│   │   Produtos    │   │Troubleshooting│
└───────┬───────┘   └───────────────┘   └───────────────┘
        │
        ├───────────────┬───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   Knowledge   │ │   Knowledge   │ │    Answer     │
│   Produtos    │ │Troubleshooting│ │               │
└───────────────┘ └───────────────┘ └───────────────┘
    """)
    
    print("\n" + "=" * 60)
    print("✅ Rede 1 Interview → 2 Knowledge criada!")
    print("=" * 60)
    
    return network


async def main():
    """Executar exemplo."""
    await demonstrate_routing()


if __name__ == "__main__":
    asyncio.run(main())
