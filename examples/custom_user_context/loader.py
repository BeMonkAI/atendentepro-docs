# -*- coding: utf-8 -*-
"""User loader for the AcmeCorp custom-context example.

The loader extracts an email from the conversation and looks the user up in a
mocked corporate directory. Returning ``None`` skips user_loading silently
(the lib tolerates this and keeps ``network.loaded_user_context`` unset).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from atendentepro.utils import extract_email_from_messages

from .context import AcmeUser


# Mocked corporate directory keyed by email. In production this would be a
# Microsoft Graph call, an LDAP lookup, an internal API, etc.
_DIRECTORY: Dict[str, Dict[str, Any]] = {
    "ana@acme.com": {
        "user_id": "ana@acme.com",
        "role": "operador",
        "empresa": "AcmeCorp Brasil",
        "aad_object_id": "8c1d7a98-9a04-4f3e-b3a8-1c87c0af0001",
        "centro_custo": "FIN-22",
        "display_name": "Ana Souza",
    },
}


def load_acme_user(messages: List[Dict[str, Any]]) -> Optional[AcmeUser]:
    """Resolve the current user from the conversation messages.

    Returns ``None`` when the user cannot be identified — the network will
    proceed without user_context (default behaviour of the library).
    """
    email = extract_email_from_messages(messages)
    if not email:
        return None

    record = _DIRECTORY.get(email.lower())
    if not record:
        return None

    return AcmeUser(
        user_id=record["user_id"],
        role=record.get("role"),
        empresa=record.get("empresa"),
        aad_object_id=record.get("aad_object_id"),
        centro_custo=record.get("centro_custo"),
        metadata={"display_name": record.get("display_name")},
    )
