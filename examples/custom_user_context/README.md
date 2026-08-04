# Custom UserContext example (AcmeCorp)

Demonstrates the **custom user context** pattern: a subclass of `UserContext` with extra fields used by client-specific tools.

See [docs/client_context_patterns.md](../../client_context_patterns.md) for the full discussion of when/why to use this pattern.

## Files

| File | Purpose |
|---|---|
| `context.py` | `AcmeUser` dataclass extending `UserContext` with `empresa`, `aad_object_id`, `centro_custo`. |
| `loader.py` | `load_acme_user(messages)` resolves the user via email lookup in a mocked corporate directory. |
| `tools.py` | `teams_escalation_transfer` tool that consumes `RunContextWrapper[AcmeUser]`. |

## How to wire it into a network

```python
from pathlib import Path

from atendentepro import create_standard_network

from docs.examples.custom_user_context.loader import load_acme_user
from docs.examples.custom_user_context.tools import teams_escalation_transfer

network = create_standard_network(
    templates_root=Path("./client_templates"),
    client="acme",
    user_loader=load_acme_user,
    custom_tools={"escalation": [teams_escalation_transfer]},
)
```

When the conversation contains `"meu email e ana@acme.com"`, the loader resolves the user and `network.loaded_user_context` becomes an `AcmeUser` instance with `empresa="AcmeCorp Brasil"` and `aad_object_id="8c1d7a98-..."`.

## Trade-offs vs. plain `UserContext.metadata`

- **Pro**: tools that need `aad_object_id` get a typed field instead of `metadata.get(...)`.
- **Pro**: typos surface at type-check time, not in production logs.
- **Con**: extra ~15 lines of code per client to maintain.

If the metadata bag is good enough for your use case, **stay with the default**. Use this pattern when you have tools that depend on specific keys and want them typed.

## Tests

There is no separate test in `tests/` because the example is intentionally pure (no network calls). The `test_user_context_examples.py` file in the lib tests covers loader behaviour with the default `UserContext`; the same patterns apply here with `AcmeUser`.
