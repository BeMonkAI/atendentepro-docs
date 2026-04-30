#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo: Executar AtendentePro com template Standard

Este exemplo mostra como usar a biblioteca atendentepro com o template padrão.
"""

import asyncio
from pathlib import Path

# Importar a biblioteca
from atendentepro import (
    create_standard_network,
    configure,
)
from agents import Runner


async def main():
    """Exemplo de uso do AtendentePro com template standard."""
    
    # 1. Configurar (opcional - usa variáveis de ambiente por padrão)
    # configure(provider="openai")
    
    # 2. Definir o caminho dos templates
    templates_root = Path(__file__).parent.parent / "client_templates"
    
    # 3. Criar a rede de agentes
    print("🔧 Criando rede de agentes...")
    network = create_standard_network(
        templates_root=templates_root,
        client="standard"
    )
    
    print("✅ Rede criada com sucesso!")
    print(f"   - Triage Agent: {network.triage.name}")
    print(f"   - Flow Agent: {network.flow.name}")
    print(f"   - Interview Agent: {network.interview.name}")
    print(f"   - Answer Agent: {network.answer.name}")
    print(f"   - Knowledge Agent: {network.knowledge.name}")
    print(f"   - Confirmation Agent: {network.confirmation.name}")
    print(f"   - Usage Agent: {network.usage.name}")
    
    # 4. Executar uma conversa simples
    print("\n💬 Iniciando conversa...")
    print("-" * 50)
    
    messages = []
    
    while True:
        try:
            user_input = input("\n👤 Você: ").strip()
            
            if user_input.lower() in ["sair", "exit", "quit", "q"]:
                print("\n👋 Até logo!")
                break
            
            if not user_input:
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            # Executar o agente de triagem
            result = await Runner.run(
                network.triage,
                messages
            )
            
            response = str(result.final_output) if result.final_output else "..."
            print(f"\n🤖 Assistente: {response}")
            
            messages.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            print("\n\n👋 Até logo!")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("  AtendentePro - Template Standard")
    print("=" * 50)
    print("\nDigite 'sair' para encerrar.\n")
    
    asyncio.run(main())

