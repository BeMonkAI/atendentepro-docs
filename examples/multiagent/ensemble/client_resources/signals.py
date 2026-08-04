# -*- coding: utf-8 -*-
"""Per-persona signal schema for the ensemble example.

Real clients keep this file at ``client_resources/signals.py`` and
declare ``output_schema: client_resources.signals.PersonaSignal`` in
``multiagent_config.yaml``. The ``output_schema`` allowlist in
:mod:`atendentepro.multiagent.metadata` gates dotted paths under the
``client_resources.`` prefix by default.

For the example we only need a single, shared schema across the three
personas — every fanout agent emits the same structured shape so the
coordinator can aggregate them uniformly.
"""

from __future__ import annotations

from atendentepro import signal_subclass

PersonaSignal = signal_subclass(
    "PersonaSignal",
    {
        # (type, default) tuples per ``signal_subclass`` contract.
        "recommendation": (str, ""),
        "horizon_months": (int, 12),
    },
)
