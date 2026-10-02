# Passo 9 (opcional): histórico replayable em multi-turn (`run_with_history`)

> **Issue:** [#119 — Runner.run does not reintroduce new_messages into the next-turn history](https://github.com/BeMonkAI/atendentepro/issues/119)

## Quando aplicar

Use este passo quando a aplicação:
- mantém conversas multi-turn em que **tools devolvem estado estruturado** (IDs, UUIDs, tokens, listas de candidatos) que precisa sobreviver para os próximos turnos;
- já tem casos em que o agente "esqueceu" um valor que tinha sido resolvido por uma tool no turno anterior — ex.: `find_report_by_name` retornou `report_template_id=...` no turno T2 e no turno T3 o agente pergunta de novo;
- está implementando um picker/wizard que coleta parâmetros iterativamente (Reports Picker, Charts Picker, Interview agent acumulando dados).

Não aplicar em chatbots single-turn ou em fluxos onde o estado é redundante com a resposta em prosa.

---

## O problema sem `run_with_history`

`Runner.run(network.triage, input)` retorna um `RunResult` cujos `new_items` carregam toda a sequência produzida na run: tool calls, tool outputs e mensagens do assistant. O padrão comum é extrair só o `final_output`:

```python
result = await Runner.run(network.triage, [{"role": "user", "content": user_msg}])
print(result.final_output)
# Tudo em result.new_items é jogado fora.
```

Isso descarta os tool outputs estruturados — o turno seguinte só recebe o histórico em prosa que o seu hub mantém, sem os IDs/UUIDs que as tools devolveram.

---

## API

```python
from atendentepro import run_with_history

result, history = await run_with_history(
    network,
    network.triage,
    messages=[{"role": "user", "content": user_msg}],
    history=history,           # None na primeira chamada
    user_id="user-123",
    session_id="conv-abc",
)
print(result.final_output)
# guarde `history` para o próximo turno
```

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `network` | `AgentNetwork` | — | Rede com `user_loader`, `memory_backend`, `history_window` opcionais. |
| `agent` | `Agent` | — | Agente de entrada (tipicamente `network.triage`). |
| `messages` | `list[dict]` | — | Mensagens **novas** deste turno (geralmente uma `{"role": "user", ...}`). Concatenadas DEPOIS de `history`. |
| `history` | `list[dict] \| None` | `None` | Histórico replayable do turno anterior. `None` na primeira chamada. |
| `**memory_kwargs` | — | — | Repassado verbatim para [`run_with_memory`](#integracao-com-run_with_memory) (`memory_backend`, `user_id`, `session_id`, etc.). |

**Retorno**: `tuple[RunResult, list[dict]]`. Salve o segundo item e passe-o como `history` na próxima chamada.

---

## Exemplo — loop de conversa

```python
from atendentepro import (
    activate, configure, create_standard_network, run_with_history,
)
from pathlib import Path

activate("seu-token")
configure(provider="openai", openai_api_key="...")
network = create_standard_network(templates_root=Path("./client_templates"), client="standard")

history: list[dict] = []
session_id = "conv-001"

while True:
    user_msg = input("> ")
    if not user_msg.strip():
        break
    result, history = await run_with_history(
        network,
        network.triage,
        messages=[{"role": "user", "content": user_msg}],
        history=history,
        user_id="user-123",
        session_id=session_id,
    )
    print(result.final_output)
```

Cada chamada:
1. Concatena `history + messages` e roda via `run_with_memory` (que aplica `user_loader`, busca de memória, `HistoryWindow` etc.).
2. Constrói `new_history = history + messages + [item.to_input_item() for item in result.new_items]` — a lista replayable que inclui tool calls e seus outputs.

O `history` retornado **não inclui** mensagens efêmeras de memória que o backend tenha injetado: elas são re-injetadas a cada turno a partir da busca, evitando duplicação no histórico de longo prazo.

---

## Integração com `run_with_memory`

`run_with_history` é um **wrapper fino** sobre `run_with_memory`. Tudo o que você usa hoje em `run_with_memory` continua valendo:

- **Memória de longo prazo** (GRKMemory) — passe `memory_backend=...` ou configure `network.memory_backend`. A busca pré-run e o save pós-run continuam acontecendo.
- **`user_loader`** — o `user_id` é resolvido do `UserContext` carregado, ou pelo parâmetro explícito.
- **`session_id_factory`** — a derivação de session_id por canal/request continua funcionando.
- **`HistoryWindow`** — se a rede tem `network.history_window`, a janela é aplicada antes do `Runner.run`. Importante: o **`history` retornado contém o histórico completo (não janelado)**; a janela é re-aplicada a cada turno.

```python
result, history = await run_with_history(
    network, network.triage,
    messages=[{"role": "user", "content": user_msg}],
    history=history,
    memory_backend=grk_backend,
    user_id="user-123",
    session_id="conv-abc",
    memory_limit=5,
    memory_threshold=0.3,
)
```

---

## Padrão de migração

Se você está migrando de `Runner.run` ou `run_with_memory` direto:

```python
# ❌ Antes — tool outputs não sobrevivem
result = await Runner.run(network.triage, conversation)
conversation.append({"role": "user", "content": next_msg})
conversation.append({"role": "assistant", "content": result.final_output})

# ✅ Depois — tool calls + outputs preservados
result, conversation = await run_with_history(
    network, network.triage,
    messages=[{"role": "user", "content": next_msg}],
    history=conversation,
)
```

---

## Limitações conhecidas

- **Stickiness de agente**: o triage continua re-roteando do zero a cada turno. Para evitar re-classificação errada em redes 3-way+, acompanhe a issue [#120](https://github.com/BeMonkAI/atendentepro/issues/120).
- **Hooks de transição entre agentes**: `HistoryWindow.on_agent_reset` só dispara quando o controle volta ao Triage; para callback em qualquer transição, acompanhe a issue [#121](https://github.com/BeMonkAI/atendentepro/issues/121).
- **Guardrail multi-turn**: `run_input_guardrails` ainda não aceita o histórico para tratar follow-ups curtos em scope checks heurísticos — issue [#122](https://github.com/BeMonkAI/atendentepro/issues/122).

---

## Referências

- API pública: `from atendentepro import run_with_history`
- Implementação: `atendentepro/memory/runner.py::run_with_history`
- Testes: `tests/test_memory_runner_run_with_history.py`
- Issue: [#119](https://github.com/BeMonkAI/atendentepro/issues/119)
