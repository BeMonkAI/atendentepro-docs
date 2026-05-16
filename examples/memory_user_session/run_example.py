#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar exemplos de user_id e session_id com memória.

Requisitos: ATENDENTEPRO_LICENSE_KEY, OPENAI_API_KEY (GRKMEMORY_API_KEY não é necessário;
os exemplos usam um backend de memória em memória).

Uso:
    python run_example.py [1|2|3|all]
    1 - user_id e session_id explícitos em run_with_memory
    2 - user_loader só dados do cliente; session_id por factory ou parâmetro
    3 - network.session_id_factory
    all - todos (padrão)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def show_menu():
    print("\n" + "=" * 60)
    print("  Memória: user_id e session_id - Exemplos")
    print("=" * 60)
    print("\n  1. user_id e session_id explícitos (run_with_memory)")
    print("  2. user_loader (só cliente); session_id por factory ou parâmetro")
    print("  3. session_id via network.session_id_factory")
    print("  4. Executar todos")
    print("  0. Sair")
    return input("\nOpção: ").strip()


async def run_one():
    from example_explicit_user_session import main as main1
    await main1()


async def run_two():
    from example_user_loader_session import main as main2
    await main2()


async def run_three():
    from example_session_id_factory import main as main3
    await main3()


async def run_all():
    await run_one()
    print("\n")
    await run_two()
    print("\n")
    await run_three()


async def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("1", "explicit"):
            await run_one()
        elif arg in ("2", "user_loader"):
            await run_two()
        elif arg in ("3", "factory"):
            await run_three()
        elif arg == "all":
            await run_all()
        else:
            print(f"Opção desconhecida: {arg}. Use 1, 2, 3 ou all.")
        return

    while True:
        choice = show_menu()
        if choice == "0":
            print("\n👋 Até logo!")
            break
        if choice == "1":
            await run_one()
        elif choice == "2":
            await run_two()
        elif choice == "3":
            await run_three()
        elif choice == "4":
            await run_all()
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
