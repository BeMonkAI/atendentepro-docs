# 20 — `context_injection`: adicionar mensagens externas ao payload

Issue [#272](https://github.com/BeMonkAI/atendentepro/issues/272) — separa o contrato *ADD* (adicionar mensagens externas a uma request especifica) do contrato *TRANSFORM* (mutar / filtrar / compactar). Ate v0.39.0, ambos viviam dentro de `pre_run_hook` (issue #195), o que mistura responsabilidades distintas.

## 20.1 — Dois contratos, dois pontos de extensao

| Operacao | API | Quando usar |
|---|---|---|
| **Transformar** o payload existente | `network.pre_run_hook` (async coroutine) | Compactar mensagens longas, filtrar PII, normalizar roles, dividir tool outputs em chunks. Hook recebe o payload e retorna o payload (possivelmente diferente). |
| **Adicionar** mensagens externas | `context_injection: List[Dict[str, Any]]` em `network.run(...)` / `run_with_memory(...)` | Long-term memory block, feature flags por request, system message com user metadata derivada de DB. Lista de mensagens declarativa, prependada ao payload. |

Sao **complementares** — `context_injection` adiciona; `pre_run_hook` ve o payload com a injecao ja aplicada e pode transformar. Cliente nao precisa mais escrever um hook so para fazer prepend.

## 20.2 — Uso em `AgentNetwork.run`

```python
from atendentepro import create_standard_network

network = create_standard_network(templates_root=Path("./client_templates"), client="my_client")

# Antes (#272) — cliente injetava manualmente:
# payload = [{"role": "system", "content": memory_block}] + payload
# result = await network.run(payload)

# Depois (#272):
result = await network.run(
    [{"role": "user", "content": user_msg}],
    context_injection=[{"role": "system", "content": memory_block}],
)
```

## 20.3a — Uso via servico multi-tenant (HTTP `/chat`)

Issue [#290](https://github.com/BeMonkAI/atendentepro/issues/290) — clientes que falam com o servidor HTTP (AIConsulta TypeScript/Deno, qualquer SaaS sobre a lib) podem passar `context_injection` direto no payload do `/chat`:

```json
POST /chat
{
  "tenant_id": "aiconsulta",
  "session_id": "conv-abc",
  "message": "queria remarcar minha consulta",
  "context_injection": [
    {"role": "system", "content": "<patient_profile>nome=Maria, ultima_consulta=2026-04-12, profissional_preferido=Dr.Silva</patient_profile>"}
  ]
}
```

Equivalente via Python:

```python
result = await mgr.chat(
    tenant_id="aiconsulta",
    session_id="conv-abc",
    message="queria remarcar minha consulta",
    context_injection=[
        {"role": "system", "content": "<patient_profile>...</patient_profile>"},
    ],
)
```

**Comportamento:**
- A lista de mensagens e PREPENDADA ao payload do runner (`Runner.run` para redes sequencias, `network.run` para ensemble).
- A injecao NAO mutaciona `session.messages` — e per-request only. Proximas chamadas nao veem a injecao do turno anterior.
- `pre_run_hook` (se setado na rede) ve a injecao + historico e pode transformar.
- `memory_context_block_tag` (build-time) funciona em paralelo — instrui os agentes a consumir o bloco.

## 20.3 — Uso em `run_with_memory` / `run_with_history`

```python
from atendentepro.memory.runner import run_with_memory

result = await run_with_memory(
    network,
    network.triage,
    [{"role": "user", "content": user_msg}],
    user_id="user-123",
    session_id="conv-abc",
    context_injection=[{"role": "system", "content": memory_block}],
)
```

`run_with_history` herda o parametro automaticamente via `**memory_kwargs`:

```python
from atendentepro import run_with_history

result, history = await run_with_history(
    network,
    network.triage,
    [{"role": "user", "content": user_msg}],
    history=history,
    context_injection=[{"role": "system", "content": memory_block}],
)
```

## 20.4 — Ordem de execucao no pipeline

`AgentNetwork.run`:

1. `context_injection` prependado ao payload
2. `pre_run_hook` (se setado) recebe o payload com a injecao
3. `Runner.run` chamado com o resultado do hook

`run_with_memory` (mais completo):

1. memory backend search + system block (se `memory_backend` setado)
2. sticky_agent_hint (se opt-in)
3. `apply_history_window` (se `history_window` setado)
4. **`context_injection` prependado** ← apos window para sobreviver ao trimming
5. `pre_run_hook` (se setado)
6. `Runner.run`

## 20.5 — Combinacao com `memory_context_block_tag` (#271)

Pattern recomendado para clientes com memoria cross-session:

```python
network = create_custom_network(
    templates_root=Path("./client_templates"),
    client="my_client",
    network_config={...},
    memory_context_block_tag="long_term_memory",  # #271: instrui agentes a LER o bloco
)

async def chat(user_id, user_msg, history):
    facts = await memory_backend.recall(user_id, limit=3)
    if facts:
        block = "<long_term_memory>\n" + "\n".join(facts) + "\n</long_term_memory>"
        injection = [{"role": "system", "content": block}]
    else:
        injection = None  # ou []

    result, history = await run_with_history(
        network,
        network.triage,
        [{"role": "user", "content": user_msg}],
        history=history,
        user_id=user_id,
        context_injection=injection,  # #272: ADICIONA a mensagem
    )
    return result.final_output, history
```

- `memory_context_block_tag` (build-time) wires todos os agentes para CONSUMIR o bloco.
- `context_injection` (call-time) ADICIONA o bloco a este request especifico.
- `pre_run_hook` (build-time) fica disponivel para TRANSFORMACOES (compactar memoria, etc).

## 20.6 — Anti-pattern: usar `pre_run_hook` so para adicionar

```python
# Errado — usar hook so para prepend e abuso de API.
async def hook(messages):
    return [{"role": "system", "content": memory_block}] + messages

network.pre_run_hook = hook

# Certo — declarativo, intencao explicita.
await network.run(messages, context_injection=[{"role": "system", "content": memory_block}])
```

Quando ler o codigo 6 meses depois, `context_injection=[...]` deixa claro que o cliente esta ADICIONANDO contexto externo. Um hook que so faz prepend e ruido que custa tempo de leitura.

## 20.7 — Defaults e backward-compat

- `context_injection=None` (default) ou `[]` → byte-for-byte identico a pre-#272.
- Input messages NUNCA sao mutadas — `network.run(messages, context_injection=...)` cria uma nova lista internamente.
- `pre_run_hook` continua vendo as mensagens injetadas — pode filtrar, transformar ou substituir.

## 20.8 — Versionamento

Disponivel a partir da v0.40.0.
