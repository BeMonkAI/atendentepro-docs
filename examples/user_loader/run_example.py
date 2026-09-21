#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar exemplos de User Loader.

Permite escolher qual exemplo executar.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from example_csv import main as csv_main
from example_database import main as db_main


def show_menu():
    """Mostra menu de opções."""
    print("\n" + "=" * 60)
    print("  User Loader - Exemplos")
    print("=" * 60)
    print("\nEscolha o exemplo:")
    print("  1. Carregamento de CSV")
    print("  2. Carregamento de Banco de Dados")
    print("  3. Executar todos")
    print("  0. Sair")
    
    choice = input("\nOpção: ").strip()
    return choice


async def main():
    """Função principal."""
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("\n👋 Até logo!")
            break
        elif choice == "1":
            await csv_main()
        elif choice == "2":
            await db_main()
        elif choice == "3":
            await csv_main()
            await db_main()
        else:
            print("\n❌ Opção inválida!")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Até logo!")
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Erro inesperado na execução do exemplo")
