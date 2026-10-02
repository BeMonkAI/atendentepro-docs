# -*- coding: utf-8 -*-
"""
Backend de memória em memória para exemplos (sem GRKMemory).

Implementa o protocolo usado por run_with_memory: search_async e save_conversation_async.
Permite rodar os exemplos de user_id/session_id sem GRKMEMORY_API_KEY.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class MockMemoryBackend:
    """
    Backend que armazena turnos por (user_id, session_id) e retorna
    um resumo nas buscas. Útil para demonstrar isolamento por usuário/sessão.
    """

    def __init__(self) -> None:
        # (user_id or "", session_id or "") -> list of saved turn summaries
        self._storage: Dict[tuple, List[str]] = {}

    async def search_async(
        self,
        query: str,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        method: str = "graph",
        limit: int = 5,
        threshold: float = 0.3,
    ) -> str:
        """Retorna as últimas memórias salvas para este user_id/session_id."""
        key = (user_id or "", session_id or "")
        entries = self._storage.get(key, [])
        if not entries:
            return ""
        # Últimas N entradas (mais recentes primeiro)
        recent = entries[-limit:] if limit else entries
        return "\n\n".join(reversed(recent))

    async def save_conversation_async(
        self,
        messages: List[Dict[str, Any]],
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Persiste um resumo do turno para este user_id/session_id."""
        key = (user_id or "", session_id or "")
        if key not in self._storage:
            self._storage[key] = []
        # Resumo simples: última mensagem do usuário + última do assistente
        parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                parts.append(f"[{role}]: {content.strip()[:200]}")
        summary = " | ".join(parts) if parts else "(turno vazio)"
        self._storage[key].append(summary)

    def get_stored_keys(self) -> List[tuple]:
        """Retorna as chaves (user_id, session_id) que têm dados (para debug)."""
        return list(self._storage.keys())
