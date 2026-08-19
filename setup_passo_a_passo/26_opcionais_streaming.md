# Passo 26 (opcional): streaming de resposta (`POST /chat/stream`)

> **Code:** `atendentepro/streaming.py`, `AgentNetwork.run_streamed`, `POST /chat/stream`.
> **Status:** opt-in (issue #492). `POST /chat` continua devolvendo o turno
> fechado. Quem nao chama o endpoint novo nao muda.

## O que e

O OpenAI Agents SDK ja tem `Runner.run_streamed()`. Este passo expoe isso
na lib e no service: o cliente web recebe tokens a medida que o agente
que **responde** gera texto, em vez de esperar o turno inteiro.

WhatsApp e canais que so entregam a mensagem fechada nao precisam deste
caminho. Continuam no `POST /chat`.

## Recorte v1

- Endpoint novo `POST /chat/stream`, body igual a `ChatRequest`.
- Resposta `text/event-stream`. Frames:

```
event: delta
data: {"text":"Hel"}

event: done
data: {"response":"Hello","agent_name":"Knowledge Agent","handoff_to":"Knowledge Agent","tool_calls":[],"tool_results":[]}
```

- `done` e o contrato canonico (mesmo shape de `POST /chat`). Deltas sao
  preview. Se houver mais de um agente depois do Triage, o texto
  streamed pode incluir um intermediario; `done.response` e sempre
  `final_output`.
- Guardrail de entrada **antes** do primeiro `delta`. Tripwire vira
  `done` com `no_reply_reason=out_of_scope` (mesmo texto branded).
- Texto do Triage (agente inicial) fica em buffer. Depois de um handoff,
  o agente seguinte streama ao vivo. Se o Triage responde sozinho, o
  buffer e enviado no fim.
- So `AgentNetwork` sequencial. `ParallelNetwork` → HTTP 400.
- Failover de provider (#490) **nao** anda neste caminho (tokens ja
  emitidos nao podem trocar de hop). `run_config=` do caller ainda vale.
- Groundedness e specialist shadow: depois do `done`, `create_task`,
  nunca reescrevem o que saiu.
- Memoria: recall continua sincrono; a geracao usa `run_streamed`; o
  save roda depois do `done`.

## Callers de biblioteca

```python
async for event in network.run_streamed(messages):
    if event.type == "delta":
        print(event.text, end="", flush=True)
    elif event.type == "done":
        print("\n", event.payload["response"])
```

## Fora do v1

Failover no meio do stream, bloqueio output-side, `stream=true` no
`/chat` existente, reconnect/`Last-Event-ID`, ensemble paralelo.
