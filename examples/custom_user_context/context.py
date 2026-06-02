# -*- coding: utf-8 -*-
"""Custom UserContext subclass for the AcmeCorp client example.

See docs/client_context_patterns.md for the full pattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from atendentepro import UserContext


@dataclass
class AcmeUser(UserContext):
    """UserContext extended with AcmeCorp directory fields.

    Inherits ``user_id``, ``role``, ``session_id`` and ``metadata`` from the
    library default. New fields default to ``None`` so the dataclass remains
    valid even when the corporate directory is partially populated.
    """

    empresa: Optional[str] = None
    aad_object_id: Optional[str] = None
    centro_custo: Optional[str] = None
