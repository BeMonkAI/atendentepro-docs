# 17 — Scheduling: per-action toggles

O agente de scheduling (`Scheduling Agent`) opt-in via `include_scheduling=True` expõe quatro ferramentas canônicas: `list_available_slots` (consulta) e três escritas — `create_appointment`, `reschedule_appointment`, `cancel_appointment`.

A partir do issue [#217](https://github.com/BeMonkAI/atendentepro/issues/217), cada **ação de escrita** é controlável individualmente via `scheduling_config.yaml`. Útil para tenants que querem IA assistente apenas para parte das ações (ex.: remarcação automática, mas sem permitir novos agendamentos pelo bot).

`list_available_slots` é read-only e **não** é toggleável.

## 17.1 — Default e backward-compat

Defaults preservam pré-#217 byte-a-byte: sem `scheduling_config.yaml`, ou com YAML antigo sem as três chaves, as três ações continuam habilitadas.

## 17.2 — Configuração

`client_templates/<tenant>/scheduling_config.yaml`:

```yaml
about: "Atendimento de agendamento do tenant X"
template: "..."
format: "..."

# Per-action toggles (todos default true).
allow_create: true
allow_reschedule: true
allow_cancel: true
```

## 17.3 — O que muda quando uma ação é desabilitada

1. **Tool filtering**: o tool correspondente é removido do tool set apresentado ao LLM. Defesa em profundidade: vale tanto para os stubs canônicos quanto para `custom_tools={"scheduling": [...]}` que reuse os nomes canônicos.
2. **Prompt** (caso misto — issue [#221](https://github.com/BeMonkAI/atendentepro/issues/221)): o agente recebe dois blocos explícitos — `[AÇÕES PERMITIDAS]` enumerando o que continua disponível e `[AÇÕES NÃO DISPONÍVEIS]` listando o que está desabilitado, seguidos de `[REGRAS DE RESTRIÇÃO]` que instruem o LLM a recusar APENAS o que está na lista de não disponíveis e a NUNCA generalizar a restrição para as demais ações.
3. **Edge case "todas off"**: quando `allow_create`, `allow_reschedule` e `allow_cancel` são todos `false`, o prompt usa um bloco `[INDISPONÍVEL]` que mantém apenas a consulta de horários e proíbe qualquer ferramenta de escrita.

## 17.4 — Cenários típicos

| Cenário | `allow_create` | `allow_reschedule` | `allow_cancel` |
|---|---|---|---|
| Tudo aberto (default) | `true` | `true` | `true` |
| Só remarcação | `false` | `true` | `false` |
| Sem cancelamento via IA | `true` | `true` | `false` |
| Apenas consulta read-only | `false` | `false` | `false` |

## 17.5 — Custom instructions

Quando o consumer passa `create_scheduling_agent(custom_instructions="...")`, os blocos `[AÇÕES PERMITIDAS]`/`[AÇÕES NÃO DISPONÍVEIS]`/`[INDISPONÍVEL]` **não** são injetados — o consumer assume responsabilidade pelo prompt. A filtragem de tools continua aplicada, então o LLM ainda não enxerga ferramentas desabilitadas.

## 17.6 — Defesa em profundidade no consumer

A filtragem de tools acontece no lado da lib. Recomendado também aplicar uma checagem no edge do consumer (ex.: replay handler) — se uma chamada chegar para um tool desabilitado (race, replay), responder `{ "success": false, "error": "<ação> não habilitada" }`.
