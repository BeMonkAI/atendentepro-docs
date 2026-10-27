# -*- coding: utf-8 -*-
"""
Exemplo: Rede com Múltiplos Agentes (2 Interview + 2 Knowledge)

Este exemplo demonstra como criar uma rede de agentes com:
- 2 Interview Agents (PF e PJ)
- 2 Knowledge Agents (Produtos PF e Soluções PJ)

Cada par Interview+Knowledge é especializado em um tipo de cliente.
"""

import asyncio
from pathlib import Path
from typing import List

from atendentepro import (
    activate,
    create_custom_network,
    create_triage_agent,
    create_interview_agent,
    create_knowledge_agent,
    create_flow_agent,
    create_answer_agent,
    create_escalation_agent,
    AgentNetwork,
)
from atendentepro.guardrails import get_guardrails_for_agent


# =============================================================================
# CONFIGURAÇÕES DOS AGENTES
# =============================================================================

# Interview PF - Coleta dados de Pessoa Física
INTERVIEW_PF_QUESTIONS = """
Para atendê-lo melhor, preciso de algumas informações:

1. **Nome completo**
2. **CPF**
3. **Data de nascimento**
4. **Renda mensal aproximada** (para oferecer as melhores condições)
5. **Produto de interesse** (conta, cartão, empréstimo, investimento)
"""

# Interview PJ - Coleta dados de Pessoa Jurídica
INTERVIEW_PJ_QUESTIONS = """
Para atendê-lo melhor, preciso de algumas informações da empresa:

1. **Razão Social**
2. **CNPJ**
3. **Faturamento anual aproximado**
4. **Número de funcionários**
5. **Segmento de atuação**
6. **Solução de interesse** (conta PJ, folha de pagamento, crédito empresarial, máquinas)
"""

# Knowledge PF - Produtos para consumidor
KNOWLEDGE_PF_ABOUT = """
Você é especialista em produtos para **Pessoa Física**:

## Produtos Disponíveis

### Conta Corrente
- Conta Digital: Gratuita, sem tarifas
- Conta Plus: R$ 29,90/mês, com benefícios premium

### Cartões
- Cartão Gold: Renda mínima R$ 3.000
- Cartão Platinum: Renda mínima R$ 8.000
- Cartão Black: Renda mínima R$ 15.000

### Empréstimos
- Empréstimo Pessoal: até R$ 50.000, taxas a partir de 1,9% a.m.
- Empréstimo Consignado: taxas a partir de 0,99% a.m.

### Investimentos
- Poupança: rendimento 0,5% a.m. + TR
- CDB: 100% do CDI, liquidez diária
- Fundos: diversos perfis de risco
"""

# Knowledge PJ - Soluções empresariais
KNOWLEDGE_PJ_ABOUT = """
Você é especialista em soluções para **Pessoa Jurídica**:

## Soluções Empresariais

### Conta Empresarial
- Conta MEI: Gratuita para microempreendedores
- Conta Empresarial: R$ 89,90/mês, pacote completo
- Conta Corporate: Sob consulta, para grandes empresas

### Folha de Pagamento
- Gestão completa de folha
- Antecipação de recebíveis
- Empréstimos consignados para funcionários

### Crédito Empresarial
- Capital de Giro: até R$ 500.000
- Antecipação de Recebíveis: taxa a partir de 1,5% a.m.
- Financiamento de Equipamentos: até 60 meses

### Máquinas de Cartão
- Maquininha Básica: Taxa 1,99% débito, 3,49% crédito
- Maquininha Pro: Taxa 1,49% débito, 2,99% crédito
- Maquininha Smart: TEF, taxa negociável
"""

# Keywords para Triage identificar o tipo
TRIAGE_KEYWORDS = """
## Palavras-chave para direcionamento

### Pessoa Física (PF)
- "pessoa física", "CPF", "cartão pessoal", "conta pessoal"
- "empréstimo pessoal", "consignado", "investimento"
- "sou eu", "para mim", "minha conta"

### Pessoa Jurídica (PJ)
- "pessoa jurídica", "CNPJ", "empresa", "empresarial"
- "folha de pagamento", "maquininha", "capital de giro"
- "MEI", "microempreendedor", "corporativo"
"""


def create_multi_agent_network() -> AgentNetwork:
    """
    Cria uma rede de agentes com múltiplos Interview e Knowledge.
    
    Arquitetura:
    
        Triage ─┬──> Interview PF ──> Knowledge PF ──> Triage
                ├──> Interview PJ ──> Knowledge PJ ──> Triage
                ├──> Flow (genérico)
                └──> Escalation
    """
    
    # =========================================================================
    # CRIAR AGENTES INDIVIDUAIS
    # =========================================================================
    
    # 1. Triage Agent (entry point)
    triage = create_triage_agent(
        keywords_text=TRIAGE_KEYWORDS,
        name="triage_agent",
    )
    
    # 2. Interview Agent - Pessoa Física
    interview_pf = create_interview_agent(
        interview_template="Atendimento Pessoa Física",
        interview_questions=INTERVIEW_PF_QUESTIONS,
        name="interview_pf",
    )
    
    # 3. Interview Agent - Pessoa Jurídica
    interview_pj = create_interview_agent(
        interview_template="Atendimento Pessoa Jurídica",
        interview_questions=INTERVIEW_PJ_QUESTIONS,
        name="interview_pj",
    )
    
    # 4. Knowledge Agent - Produtos PF
    knowledge_pf = create_knowledge_agent(
        knowledge_about=KNOWLEDGE_PF_ABOUT,
        knowledge_template="Produtos para Pessoa Física",
        knowledge_format="Responda de forma clara e objetiva.",
        name="knowledge_pf",
        single_reply=True,  # Responde uma vez e volta ao triage
    )
    
    # 5. Knowledge Agent - Soluções PJ
    knowledge_pj = create_knowledge_agent(
        knowledge_about=KNOWLEDGE_PJ_ABOUT,
        knowledge_template="Soluções Empresariais",
        knowledge_format="Responda de forma profissional e detalhada.",
        name="knowledge_pj",
        single_reply=True,  # Responde uma vez e volta ao triage
    )
    
    # 6. Flow Agent (genérico para ambos)
    flow = create_flow_agent(
        flow_template="Atendimento",
        flow_keywords="",
        name="flow_agent",
    )
    
    # 7. Answer Agent
    answer = create_answer_agent(
        answer_template="",
        name="answer_agent",
    )
    
    # 8. Escalation Agent
    escalation = create_escalation_agent(
        escalation_channels="Atendimento humano disponível de segunda a sexta, 8h às 18h.",
        name="escalation_agent",
    )
    
    # =========================================================================
    # CONFIGURAR HANDOFFS
    # =========================================================================
    
    # Triage pode direcionar para qualquer agente especializado
    triage.handoffs = [
        interview_pf,  # Para clientes PF
        interview_pj,  # Para clientes PJ
        knowledge_pf,  # Consultas diretas sobre produtos PF
        knowledge_pj,  # Consultas diretas sobre soluções PJ
        flow,          # Fluxo genérico
        escalation,    # Escalar para humano
    ]
    
    # Interview PF -> Knowledge PF ou Triage
    interview_pf.handoffs = [
        knowledge_pf,  # Após coletar dados, buscar produtos
        answer,        # Responder com base nos dados
        triage,        # Voltar ao início
        escalation,    # Escalar se necessário
    ]
    
    # Interview PJ -> Knowledge PJ ou Triage
    interview_pj.handoffs = [
        knowledge_pj,  # Após coletar dados, buscar soluções
        answer,        # Responder com base nos dados
        triage,        # Voltar ao início
        escalation,    # Escalar se necessário
    ]
    
    # Knowledge PF -> Triage (single_reply já configurado)
    knowledge_pf.handoffs = [triage, escalation]
    
    # Knowledge PJ -> Triage (single_reply já configurado)
    knowledge_pj.handoffs = [triage, escalation]
    
    # Flow -> Interview ou Triage
    flow.handoffs = [interview_pf, interview_pj, triage, escalation]
    
    # Answer -> Triage
    answer.handoffs = [triage, escalation]
    
    # Escalation -> Triage
    escalation.handoffs = [triage]
    
    # =========================================================================
    # CRIAR NETWORK CUSTOMIZADA
    # =========================================================================
    
    network = create_custom_network(
        triage=triage,
        custom_agents={
            "interview_pf": interview_pf,
            "interview_pj": interview_pj,
            "knowledge_pf": knowledge_pf,
            "knowledge_pj": knowledge_pj,
            "flow": flow,
            "answer": answer,
            "escalation": escalation,
        },
    )
    
    return network


async def demonstrate_routing():
    """
    Demonstra como o Triage direciona para diferentes agentes.
    """
    print("\n" + "=" * 60)
    print("🔀 Exemplo: Múltiplos Agentes (2 Interview + 2 Knowledge)")
    print("=" * 60)
    
    network = create_multi_agent_network()
    
    # Listar todos os agentes
    print("\n📋 Agentes na rede:")
    for agent in network.get_all_agents():
        handoff_names = [h.name for h in getattr(agent, 'handoffs', [])]
        print(f"   - {agent.name}")
        if handoff_names:
            print(f"     └─ handoffs: {', '.join(handoff_names)}")
    
    # Demonstrar cenários
    print("\n" + "-" * 40)
    print("📌 Cenários de Roteamento:")
    print("-" * 40)
    
    scenarios = [
        ("Quero abrir uma conta para mim", "interview_pf → knowledge_pf"),
        ("Preciso de um cartão de crédito pessoal", "knowledge_pf (direto)"),
        ("Minha empresa precisa de maquininha", "interview_pj → knowledge_pj"),
        ("Quero folha de pagamento para 50 funcionários", "interview_pj → knowledge_pj"),
        ("Quero falar com um atendente humano", "escalation"),
    ]
    
    for mensagem, rota_esperada in scenarios:
        print(f"\n💬 '{mensagem}'")
        print(f"   → Rota esperada: {rota_esperada}")
    
    print("\n" + "=" * 60)
    print("✅ Rede multi-agentes criada com sucesso!")
    print("=" * 60)
    
    return network


async def main():
    """Executar exemplo."""
    await demonstrate_routing()


if __name__ == "__main__":
    asyncio.run(main())
