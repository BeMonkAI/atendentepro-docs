# 15 — Hooks de runtime: `pre_run_hook` + `end_session`

Dois pontos de extensão adicionados na v0.30.0 para integrações que precisam de **contexto dinâmico por request** (`pre_run_hook` — issue #195) e **ciclo de vida de sessão** (`end_session` + `MemoryBackend.on_session_end` — issue #197). Ambos são opt-in; não setá-los preserva o comportamento anterior byte-a-byte.

## 15.1 — `pre_run_hook` (issue #195)

`AgentNetwork.pre_run_hook` é uma corrotina opcional `async (messages) -> messages` invocada por `network.run(...)` e por `run_with_memory(...)` **logo antes** do `Runner.run`. É o ponto canônico para:

- Injetar feature flags ou dados de sessão carregados assincronamente.
- Pré-processar mensagens (ex: truncar conteúdo sensível, anexar metadata).
- Decorar a última mensagem do usuário com contexto que muda a cada turno.

Quando `pre_run_hook=None` (default), o caminho de execução é idêntico à v0.29.x.

```python
from atendentepro import create_standard_network

async def inject_session_flags(messages):
    flags = await fetch_feature_flags(...)  # I/O assíncrono
    return [
        {"role": "system", "content": f"[Flags] {flags}"},
        *messages,
    ]

network = create_standard_network(templates_root=..., client="acme")
network.pre_run_hook = inject_session_flags

# Vai chamar inject_session_flags(messages) antes de Runner.run
result = await network.run([{"role": "user", "content": "Oi"}])
```

Regras:

- A função **deve retornar** a lista de mensagens (mesmo que mutada in place). Retornar `None` levanta `TypeError` para falhar alto — silenciar erros aqui significaria conversa vazia sendo enviada ao LLM.
- Em `run_with_memory`, o hook roda **depois** de memory enrichment, sticky-agent hint e `HistoryWindow`, garantindo que o hook veja a mesma lista que vai chegar no LLM.
- Não use o hook para fazer roteamento — para isso existem `sticky_agent_hint` e os agentes de Triage. O hook é exclusivamente para **transformar mensagens**.

Para chamar fora de `network.run`/`run_with_memory` (em integrações custom), use o helper exportado:

```python
from atendentepro import apply_pre_run_hook

messages = await apply_pre_run_hook(network, messages)
```

## 15.2 — `MemoryBackend.on_session_end` + `end_session` (issue #197)

Clientes que precisam consolidar/sumarizar uma sessão **quando o cliente decide que ela terminou** (idle timeout, encerramento de canal, fim de janela de atendimento) agora têm um ponto canônico:

1. `MemoryBackend.on_session_end(session_id, user_id, turns)` — método opcional declarado no Protocol. `GRKMemoryBackend` traz implementação no-op por padrão; subclasse e sobrescreva para consolidar.
2. `atendentepro.end_session(network, session_id=..., user_id=..., turns=...)` — helper que resolve o backend (param explícito → `network.memory_backend`) e dispara o hook de forma defensiva (no-op se backend ausente ou não implementa).

A biblioteca **não detecta inatividade** — isso é responsabilidade do cliente, que tipicamente já gerencia state de canal/conexão. A lib só fornece a superfície do hook.

```python
from atendentepro import end_session

# Quando seu serviço decide que a sessão terminou:
await end_session(
    network,
    session_id="conv-abc",
    user_id="user-123",
    turns=current_session_messages,  # opcional
)
```

Implementação custom:

```python
from atendentepro import GRKMemoryBackend

class MyBackend(GRKMemoryBackend):
    async def on_session_end(self, *, session_id, user_id=None, turns=None):
        summary = await self._summarize(turns or [])
        await self._grk.save_summary_async(
            summary, user_id=user_id, session_id=session_id,
        )

network.memory_backend = MyBackend(grk_instance=...)
```

## 15.3 — `AgentNetwork.memory_backend` é campo tipado (issue #196)

Antes da v0.30.0, `network.memory_backend = backend` era atribuição dinâmica — type checkers e IDE não enxergavam. Agora é um campo declarado `Optional[MemoryBackend] = None` no dataclass, com autocomplete e validação de tipo.
