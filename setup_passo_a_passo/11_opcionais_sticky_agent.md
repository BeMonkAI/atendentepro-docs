# Passo 11 (opcional): stickiness de agente entre turnos (`sticky_agent_hint`)

> **Issue:** [#120 — Network has no agent stickiness across turns](https://github.com/BeMonkAI/atendentepro/issues/120)

## Quando aplicar

Use este passo quando a aplicação:

- usa rede 3-way+ (`triage` → `{flow, interview, knowledge}`) e o usuário coleta parâmetros iterativamente (Reports/Charts Picker, Interview agent, wizards);
- já viu re-roteamentos espúrios do Triage no meio de um fluxo: turno T2 fica em Knowledge, T3 vai para Flow, T4 volta para Knowledge — perdendo contexto a cada salto;
- deseja que o Triage, na ausência de mudança clara de intenção, **mantenha** o agente que estava ativo no turno anterior.

Não aplicar em chatbots single-turn ou em redes de 1-2 agentes.

---

## O que muda

`Runner.run(network.triage, ...)` sempre parte do Triage e re-classifica o input do zero a cada turno. Sem nenhuma noção de "agente ativo no turno anterior", o Triage pode rotear errado quando o usuário fragmenta a intenção ao longo de várias mensagens curtas.

Com `sticky_agent_hint=True`, o `run_with_memory` (e portanto `run_with_history`) **prepende uma mensagem `system` curta** ao input antes de chamar `Runner.run`:

```
[Roteamento] Agente ativo no turno anterior: Knowledge Agent.
Mantenha esse agente a menos que a intencao do usuario tenha mudado claramente.
```

O Triage, pelo OpenAI Chat API, dá alta prioridade a mensagens `system` e usa essa pista na decisão de routing — sem precisar mexer nas instruções fixas do Triage nem rebuilder o agente a cada turno.

---

## API

```python
from pathlib import Path
from atendentepro import create_standard_network

network = create_standard_network(
    templates_root=Path("./client_templates"),
    client="meu_cliente",
)

network.sticky_agent_hint = True   # opt-in, default False
```

`network.last_agent_name` (já existente desde a v0.21, atualizado por `run_with_memory` após cada `Runner.run`) é a fonte do nome injetado no hint.

| Field | Tipo | Default | Descrição |
|---|---|---|---|
| `sticky_agent_hint` | `bool` | `False` | Opt-in. Quando `True`, ativa a injeção do hint a cada turno. |
| `last_agent_name` | `Optional[str]` | `None` | Tracking automático: nome do agente que produziu output no turno anterior. Só usado quando `sticky_agent_hint=True`. |

---

## Quando o hint NÃO é injetado

A função `_build_sticky_agent_hint` retorna `None` (sem hint) nos seguintes casos:

| Condição | Motivo |
|---|---|
| `sticky_agent_hint=False` | Não opt-in. |
| `last_agent_name is None` | Primeiro turno da sessão — nada para enviesar. |
| `last_agent_name` em branco | Defesa contra strings vazias. |
| `last_agent_name` começa com `"triage"` (case-insensitive) | Triage já foi o último — nada para enviesar (continua no Triage normalmente). |

---

## Exemplo — wizard de Reports Picker

```python
from atendentepro import (
    activate, configure, create_standard_network, run_with_history,
)
from pathlib import Path

activate("seu-token")
configure(provider="openai", openai_api_key="...")
network = create_standard_network(templates_root=Path("./client_templates"), client="meu_cliente")
network.sticky_agent_hint = True   # liga a stickiness

history: list[dict] = []
session_id = "conv-001"

# T1: usuário pede um reporte
result, history = await run_with_history(
    network, network.triage,
    messages=[{"role": "user", "content": "quero um reporte"}],
    history=history,
    session_id=session_id,
    user_id="user-123",
)
# Triage → Knowledge (lista os reports)
# network.last_agent_name = "Knowledge Agent"

# T2: usuário escolhe — sticky hint diz "fica em Knowledge"
result, history = await run_with_history(
    network, network.triage,
    messages=[{"role": "user", "content": "Deep-Dive"}],
    history=history,
    session_id=session_id,
    user_id="user-123",
)
# Triage vê "[Roteamento] Agente ativo no turno anterior: Knowledge Agent..."
# e mantém Knowledge para o follow-up "Deep-Dive"

# T3: pergunta colateral que sem stickiness viraria Flow
result, history = await run_with_history(
    network, network.triage,
    messages=[{"role": "user", "content": "quais marcas tem?"}],
    history=history,
    session_id=session_id,
    user_id="user-123",
)
# Sem sticky: Triage roteava para Flow porque "marcas" é keyword analítica.
# Com sticky: hint indica Knowledge ainda ativo → Knowledge atende a pergunta
# dentro do contexto do report sendo configurado.
```

---

## Composição com outras camadas

A ordem de `system` messages prepended ao input do Triage:

1. **Sticky-agent hint** (issue #120) — quando `sticky_agent_hint=True`
2. **Memory block** (`network.memory_backend`) — quando há contexto de longo prazo recuperado
3. **HistoryWindow** — truncamento/sumarização aplicados em cima de tudo

Sticky hint vem primeiro porque é a pista de **roteamento** (decisão estrutural). Memória vem depois (contexto factual). Tudo acontece dentro de `run_with_memory` / `run_with_history`.

---

## Limitações conhecidas

- **Hint é apenas uma pista** — o Triage continua sendo um LLM que pode contrariar quando a mudança de intenção é clara. Se você precisa de roteamento determinístico, isso ainda é possível via implementação de `network_type='custom_module'` (issue #87) com lógica de stickiness explícita.
- **Não persiste cross-session** — se você descarta o objeto `network` entre requests (factory pattern), `last_agent_name` zera. Para web apps stateless, persista o último agente externamente (Redis, DB) e injete via `network.last_agent_name = ...` antes de cada chamada.
- **Não cobre transições intermediárias** — se você quiser um callback em cada handoff entre agentes, acompanhe a issue [#121](https://github.com/BeMonkAI/atendentepro/issues/121) (`HistoryWindow.on_agent_switch`).

---

## Referências

- API pública: campo `AgentNetwork.sticky_agent_hint`
- Implementação: `atendentepro/memory/runner.py::_build_sticky_agent_hint`
- Testes: `tests/test_memory_runner_sticky_agent.py`
- Issue: [#120](https://github.com/BeMonkAI/atendentepro/issues/120)
