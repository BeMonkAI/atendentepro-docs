#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar os exemplos de Filtros de Acesso.

Usage:
    python run_example.py [code|yaml|all]
    
    code - Executa exemplo via código Python
    yaml - Executa exemplo via YAML
    all  - Executa todos (padrão)
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


async def run_code_example():
    """Executar exemplo via código."""
    from example_via_code import main
    await main()


async def run_yaml_example():
    """Executar exemplo via YAML."""
    from example_via_yaml import main
    await main()


async def main():
    """Executar exemplos baseado no argumento."""
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    print("=" * 60)
    print("🔐 Access Filters - Exemplos")
    print("=" * 60)
    print(f"Modo: {mode}")
    print()
    
    if mode in ("code", "all"):
        await run_code_example()
    
    if mode in ("yaml", "all"):
        await run_yaml_example()
    
    print("\n" + "=" * 60)
    print("🎉 Execução concluída!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
