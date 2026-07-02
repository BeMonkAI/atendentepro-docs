# -*- coding: utf-8 -*-
"""Custom tools that consume the AcmeUser context.

Tools declare ``RunContextWrapper[AcmeUser]`` so the new fields are typed.
Library tools (RAG, escalation default, ...) keep using
``RunContextWrapper[UserContext]`` and continue to work because
``AcmeUser`` inherits from ``UserContext``.
"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from .context import AcmeUser


@function_tool
async def teams_escalation_transfer(
    wrapper: RunContextWrapper[AcmeUser],
    motivo: str,
) -> str:
    """Forward an issue to the operator's supervisor in Teams.

    Returns a deterministic, human-readable status string. The real
    implementation would create an Adaptive Card via the Graph API.
    """
    user = wrapper.context
    if user.aad_object_id is None:
        return "Nao foi possivel escalar: usuario nao identificado no diretorio corporativo."

    return (
        f"Escalonado para o supervisor de {user.empresa or 'unidade nao identificada'} "
        f"(AAD={user.aad_object_id}, motivo={motivo})."
    )
