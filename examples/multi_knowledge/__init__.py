# -*- coding: utf-8 -*-
"""
Multi-Knowledge Example Client

Exemplo de cliente que utiliza múltiplos Knowledge Agents especializados:
- Knowledge Técnico: Documentação técnica, manuais, especificações
- Knowledge FAQ: Perguntas frequentes, tutoriais, guias
- Knowledge Políticas: Termos, políticas, procedimentos internos

Cada Knowledge Agent tem sua própria base de embeddings e especialização.
"""

from .network import (
    create_multi_knowledge_network,
    MultiKnowledgeNetwork,
)

__all__ = [
    "create_multi_knowledge_network",
    "MultiKnowledgeNetwork",
]

