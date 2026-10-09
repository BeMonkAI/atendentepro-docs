#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar o exemplo de múltiplos agentes.

Usage:
    python run_example.py
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


async def main():
    """Executar exemplo."""
    from example_multi_agents import main as run_demo
    await run_demo()


if __name__ == "__main__":
    asyncio.run(main())
