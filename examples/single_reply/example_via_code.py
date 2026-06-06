# -*- coding: utf-8 -*-
"""
Exemplo: Configurando Single Reply Mode via código Python.

Este exemplo mostra como ativar o modo de resposta única
diretamente no código, sem usar arquivos YAML.
"""

import asyncio
from pathlib import Path

from atendentepro import activate, create_standard_network


async def exemplo_global_single_reply():
    """
    Exemplo 1: Ativar single_reply para TODOS os agentes.
    
    Útil quando você quer um chatbot extremamente direto,
    onde cada interação é independente.
    """
    print("\n" + "=" * 60)
    print("Exemplo 1: Global Single Reply (todos os agentes)")
    print("=" * 60)
    
    network = create_standard_network(
        templates_root=Path(__file__).parent,
        client="config",
        # Todos os agentes respondem uma vez e voltam ao Triage
        global_single_reply=True,
    )
    
    print("\n✅ Network criada com global_single_reply=True")
    print("📋 Todos os agentes responderão uma vez e voltarão ao Triage")
    
    return network


async def exemplo_single_reply_seletivo():
    """
    Exemplo 2: Ativar single_reply apenas para agentes específicos.
    
    Configuração mais comum: agentes de consulta (Knowledge, Answer)
    respondem uma vez, enquanto agentes de coleta (Interview, Onboarding)
    podem ter múltiplas interações.
    """
    print("\n" + "=" * 60)
    print("Exemplo 2: Single Reply Seletivo (por agente)")
    print("=" * 60)
    
    network = create_standard_network(
        templates_root=Path(__file__).parent,
        client="config",
        global_single_reply=False,  # Não global
        single_reply_agents={
            # Agentes de consulta: respondem uma vez
            "knowledge": True,
            "answer": True,
            "confirmation": True,
            "usage": True,
            
            # Agentes de coleta: múltiplas interações
            "interview": False,
            "onboarding": False,
            
            # Flow geralmente apresenta opções uma vez
            "flow": True,
            
            # Escalation/Feedback: registra e volta
            "escalation": True,
            "feedback": True,
        },
    )
    
    print("\n✅ Network criada com single_reply seletivo")
    print("📋 Configuração:")
    print("   - Knowledge, Answer, Confirmation: single_reply=True")
    print("   - Interview, Onboarding: single_reply=False")
    
    return network


async def exemplo_faq_bot():
    """
    Exemplo 3: Chatbot de FAQ otimizado.
    
    Perfeito para sites de e-commerce, suporte técnico, etc.
    Cada pergunta é tratada independentemente.
    """
    print("\n" + "=" * 60)
    print("Exemplo 3: FAQ Bot (Knowledge + Answer com single_reply)")
    print("=" * 60)
    
    network = create_standard_network(
        templates_root=Path(__file__).parent,
        client="config",
        global_single_reply=False,
        single_reply_agents={
            "knowledge": True,  # FAQ: responde e volta
            "answer": True,     # Perguntas gerais: responde e volta
            "flow": True,       # Menu: apresenta e volta
            # Outros agentes mantêm comportamento padrão
        },
    )
    
    print("\n✅ FAQ Bot criado")
    print("📋 Fluxo típico:")
    print("   1. Usuário faz pergunta")
    print("   2. Triage direciona para Knowledge/Answer")
    print("   3. Agente responde UMA vez")
    print("   4. Retorna ao Triage para próxima pergunta")
    
    return network


async def exemplo_coleta_de_leads():
    """
    Exemplo 4: Bot de coleta de leads/cadastro.
    
    Interview precisa de múltiplas interações para coletar dados,
    mas outros agentes podem responder rapidamente.
    """
    print("\n" + "=" * 60)
    print("Exemplo 4: Bot de Coleta de Leads")
    print("=" * 60)
    
    network = create_standard_network(
        templates_root=Path(__file__).parent,
        client="config",
        global_single_reply=False,
        single_reply_agents={
            # Interview PRECISA de múltiplas interações
            "interview": False,
            
            # Outros agentes podem ser rápidos
            "knowledge": True,   # Tira dúvidas sobre produto
            "answer": True,      # Responde perguntas
            "confirmation": True, # Confirma cadastro
        },
    )
    
    print("\n✅ Bot de Leads criado")
    print("📋 Fluxo típico:")
    print("   1. Triage detecta interesse")
    print("   2. Interview coleta: nome, email, telefone (múltiplas msgs)")
    print("   3. Confirmation confirma dados (single_reply)")
    print("   4. Retorna ao Triage")
    
    return network


async def main():
    """Executar todos os exemplos."""
    # Ativar biblioteca (substitua pela sua chave)
    # activate("ATP_sua-chave-aqui")
    
    print("🔁 Exemplos de Single Reply Mode")
    print("=" * 60)
    
    # Executar exemplos (sem realmente iniciar conversação)
    await exemplo_global_single_reply()
    await exemplo_single_reply_seletivo()
    await exemplo_faq_bot()
    await exemplo_coleta_de_leads()
    
    print("\n" + "=" * 60)
    print("✅ Todos os exemplos executados com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
