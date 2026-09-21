# -*- coding: utf-8 -*-
"""
Multi-Knowledge Network Configuration

Este exemplo demonstra como criar uma rede de agentes com múltiplos
Knowledge Agents especializados em diferentes bases de conhecimento.

Arquitetura:
                          ┌─────────────────┐
                          │     Triage      │
                          └────────┬────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ Knowledge       │  │ Knowledge       │  │ Knowledge       │
    │ Técnico         │  │ FAQ             │  │ Políticas       │
    │ (Manuais)       │  │ (Tutoriais)     │  │ (Termos)        │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from agents import Agent

from atendentepro import activate
from atendentepro.agents import (
    create_triage_agent,
    create_flow_agent,
    create_interview_agent,
    create_answer_agent,
    create_knowledge_agent,
    create_escalation_agent,
    create_feedback_agent,
    KnowledgeAgent,
)
from atendentepro.models import ContextNote
from atendentepro.config import RECOMMENDED_PROMPT_PREFIX


@dataclass
class MultiKnowledgeNetwork:
    """
    Rede de agentes com múltiplos Knowledge Agents.
    
    Attributes:
        triage: Agente de triagem (ponto de entrada)
        flow: Agente de fluxo conversacional
        interview: Agente de entrevista
        answer: Agente de resposta
        knowledge_tecnico: Knowledge Agent para documentação técnica
        knowledge_faq: Knowledge Agent para FAQs e tutoriais
        knowledge_politicas: Knowledge Agent para políticas e termos
        escalation: Agente de escalonamento
        feedback: Agente de feedback
    """
    triage: Agent[ContextNote]
    flow: Agent[ContextNote]
    interview: Agent[ContextNote]
    answer: Agent[ContextNote]
    knowledge_tecnico: KnowledgeAgent
    knowledge_faq: KnowledgeAgent
    knowledge_politicas: KnowledgeAgent
    escalation: Optional[Agent[ContextNote]] = None
    feedback: Optional[Agent[ContextNote]] = None
    
    def get_all_knowledge_agents(self) -> List[KnowledgeAgent]:
        """Retorna lista de todos os Knowledge Agents."""
        return [
            self.knowledge_tecnico,
            self.knowledge_faq,
            self.knowledge_politicas,
        ]


def create_multi_knowledge_network(
    templates_root: Path,
    client: str = "multi_knowledge_example",
    # Paths para embeddings de cada knowledge base
    embeddings_tecnico: Optional[Path] = None,
    embeddings_faq: Optional[Path] = None,
    embeddings_politicas: Optional[Path] = None,
    # Configurações opcionais
    include_escalation: bool = True,
    include_feedback: bool = True,
) -> MultiKnowledgeNetwork:
    """
    Cria uma rede de agentes com múltiplos Knowledge Agents.
    
    Args:
        templates_root: Diretório raiz dos templates
        client: Nome do cliente
        embeddings_tecnico: Path para embeddings de documentação técnica
        embeddings_faq: Path para embeddings de FAQs
        embeddings_politicas: Path para embeddings de políticas
        include_escalation: Incluir agente de escalonamento
        include_feedback: Incluir agente de feedback
        
    Returns:
        MultiKnowledgeNetwork configurada
        
    Example:
        >>> network = create_multi_knowledge_network(
        ...     templates_root=Path("./templates"),
        ...     embeddings_tecnico=Path("./data/tecnico_embeddings.pkl"),
        ...     embeddings_faq=Path("./data/faq_embeddings.pkl"),
        ...     embeddings_politicas=Path("./data/politicas_embeddings.pkl"),
        ... )
        >>> # Usar o triage como ponto de entrada
        >>> result = await Runner.run(network.triage, messages)
    """
    
    # =========================================================================
    # 1. CRIAR OS MÚLTIPLOS KNOWLEDGE AGENTS
    # =========================================================================
    
    # Knowledge Técnico - Documentação, manuais, especificações
    knowledge_tecnico = create_knowledge_agent(
        name="Knowledge Técnico",
        knowledge_about="""
        Base de conhecimento técnico contendo:
        - Manuais de produtos e serviços
        - Documentação técnica detalhada
        - Especificações e fichas técnicas
        - Guias de instalação e configuração
        - Troubleshooting técnico
        """,
        knowledge_template="Documento técnico: {titulo} | Categoria: {categoria}",
        knowledge_format="Responda com detalhes técnicos precisos, incluindo passos numerados quando aplicável.",
        embeddings_path=embeddings_tecnico,
        include_rag_tool=embeddings_tecnico is not None,
        custom_instructions="""
        Você é o Knowledge Agent TÉCNICO, especializado em documentação técnica.
        
        Sua especialidade:
        - Manuais de produtos
        - Especificações técnicas
        - Guias de instalação
        - Procedimentos de troubleshooting
        
        Quando responder:
        1. Seja preciso e técnico
        2. Use terminologia correta
        3. Inclua passos numerados
        4. Cite o documento fonte
        
        Se a pergunta NÃO for técnica, transfira para o Triage Agent.
        """,
    )
    
    # Knowledge FAQ - Perguntas frequentes, tutoriais
    knowledge_faq = create_knowledge_agent(
        name="Knowledge FAQ",
        knowledge_about="""
        Base de conhecimento de FAQs contendo:
        - Perguntas frequentes dos clientes
        - Tutoriais passo-a-passo
        - Guias de uso rápido
        - Dicas e melhores práticas
        - Soluções para problemas comuns
        """,
        knowledge_template="FAQ: {pergunta} | Categoria: {categoria}",
        knowledge_format="Responda de forma clara e acessível, como se estivesse explicando para um usuário iniciante.",
        embeddings_path=embeddings_faq,
        include_rag_tool=embeddings_faq is not None,
        custom_instructions="""
        Você é o Knowledge Agent FAQ, especializado em perguntas frequentes.
        
        Sua especialidade:
        - Perguntas comuns dos clientes
        - Tutoriais simples
        - Dicas de uso
        - Soluções rápidas
        
        Quando responder:
        1. Use linguagem simples e acessível
        2. Evite jargões técnicos
        3. Dê exemplos práticos
        4. Seja conciso
        
        Se a pergunta for muito técnica, transfira para o Knowledge Técnico.
        Se for sobre políticas/termos, transfira para o Knowledge Políticas.
        """,
    )
    
    # Knowledge Políticas - Termos, políticas, procedimentos
    knowledge_politicas = create_knowledge_agent(
        name="Knowledge Políticas",
        knowledge_about="""
        Base de conhecimento de políticas contendo:
        - Termos de uso e serviço
        - Política de privacidade
        - Política de reembolso e cancelamento
        - Procedimentos internos
        - Contratos e SLAs
        - Compliance e regulamentações
        """,
        knowledge_template="Política: {titulo} | Vigência: {data}",
        knowledge_format="Responda citando os termos oficiais. Use linguagem formal e precisa.",
        embeddings_path=embeddings_politicas,
        include_rag_tool=embeddings_politicas is not None,
        custom_instructions="""
        Você é o Knowledge Agent POLÍTICAS, especializado em termos e políticas.
        
        Sua especialidade:
        - Termos de uso
        - Políticas de privacidade
        - Regras de reembolso
        - Procedimentos oficiais
        - Compliance
        
        Quando responder:
        1. Cite os termos exatos quando possível
        2. Use linguagem formal
        3. Seja preciso sobre datas e condições
        4. Indique a versão/data do documento
        
        Se a pergunta for técnica, transfira para o Knowledge Técnico.
        Se for uma dúvida comum, transfira para o Knowledge FAQ.
        """,
    )
    
    # =========================================================================
    # 2. CRIAR OS DEMAIS AGENTES
    # =========================================================================
    
    triage = create_triage_agent(
        keywords_text="""
        # Keywords para roteamento de Knowledge Agents
        
        ## Knowledge Técnico
        - manual, documentação, especificação, técnico
        - instalação, configuração, setup
        - erro, bug, problema técnico, troubleshooting
        - API, integração, SDK
        
        ## Knowledge FAQ
        - como fazer, como funciona, tutorial
        - dúvida, pergunta, ajuda
        - dica, melhor forma, recomendação
        
        ## Knowledge Políticas
        - termos, política, privacidade
        - reembolso, cancelamento, devolução
        - contrato, SLA, garantia
        - LGPD, compliance, regulamento
        """,
    )
    
    flow = create_flow_agent()
    interview = create_interview_agent()
    answer = create_answer_agent()
    
    # Escalation e Feedback opcionais
    escalation = None
    feedback = None
    
    if include_escalation:
        escalation = create_escalation_agent(
            escalation_channels="Telefone: 0800-XXX-XXXX | Email: suporte@empresa.com | Chat ao vivo",
        )
    
    if include_feedback:
        feedback = create_feedback_agent(
            protocol_prefix="MK",
            email_brand_name="Multi-Knowledge Example",
        )
    
    # =========================================================================
    # 3. CONFIGURAR HANDOFFS
    # =========================================================================
    
    # Triage pode ir para qualquer Knowledge Agent + Flow
    triage_handoffs = [
        knowledge_tecnico,
        knowledge_faq,
        knowledge_politicas,
        flow,
    ]
    
    # Cada Knowledge pode voltar para Triage ou ir para outro Knowledge
    knowledge_handoffs = [triage, knowledge_tecnico, knowledge_faq, knowledge_politicas]
    
    # Flow segue o fluxo normal
    flow_handoffs = [interview, triage]
    interview_handoffs = [answer]
    answer_handoffs = [triage]
    
    # Adicionar Escalation e Feedback a todos se habilitados
    if escalation:
        triage_handoffs.append(escalation)
        knowledge_handoffs.append(escalation)
        flow_handoffs.append(escalation)
        interview_handoffs.append(escalation)
        answer_handoffs.append(escalation)
    
    if feedback:
        triage_handoffs.append(feedback)
        knowledge_handoffs.append(feedback)
        flow_handoffs.append(feedback)
        interview_handoffs.append(feedback)
        answer_handoffs.append(feedback)
    
    # Aplicar handoffs
    triage.handoffs = triage_handoffs
    knowledge_tecnico.handoffs = knowledge_handoffs.copy()
    knowledge_faq.handoffs = knowledge_handoffs.copy()
    knowledge_politicas.handoffs = knowledge_handoffs.copy()
    flow.handoffs = flow_handoffs
    interview.handoffs = interview_handoffs
    answer.handoffs = answer_handoffs
    
    if escalation:
        escalation.handoffs = [triage, feedback] if feedback else [triage]
    if feedback:
        feedback.handoffs = [triage, escalation] if escalation else [triage]
    
    # =========================================================================
    # 4. RETORNAR A REDE
    # =========================================================================
    
    return MultiKnowledgeNetwork(
        triage=triage,
        flow=flow,
        interview=interview,
        answer=answer,
        knowledge_tecnico=knowledge_tecnico,
        knowledge_faq=knowledge_faq,
        knowledge_politicas=knowledge_politicas,
        escalation=escalation,
        feedback=feedback,
    )


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    from agents import Runner
    
    async def main():
        # Ativar a biblioteca
        activate("ATP_seu-token-aqui")
        
        # Criar a rede com múltiplos knowledge
        network = create_multi_knowledge_network(
            templates_root=Path("./templates"),
            # Paths para os embeddings (opcional - pode funcionar sem RAG)
            embeddings_tecnico=Path("./data/tecnico_embeddings.pkl"),
            embeddings_faq=Path("./data/faq_embeddings.pkl"),
            embeddings_politicas=Path("./data/politicas_embeddings.pkl"),
        )
        
        print("Rede criada com sucesso!")
        print(f"Knowledge Agents disponíveis:")
        for ka in network.get_all_knowledge_agents():
            print(f"  - {ka.name}")
        
        # Exemplo de conversa
        messages = [
            {"role": "user", "content": "Como faço para cancelar minha assinatura?"}
        ]
        
        result = await Runner.run(network.triage, messages)
        print(f"\nResposta: {result.final_output}")
    
    asyncio.run(main())

