# 27. Opcional: despacho de jobs assíncronos

Permite que um agente entregue uma tarefa longa a um serviço de jobs HTTP
externo e acompanhe o resultado, em vez de tentar resolvê-la dentro do turno
da conversa. O padrão é o clássico de job assíncrono: cria, recebe um id,
consulta.

É **opt-in**. Sem as variáveis de ambiente e sem o wiring abaixo, nada muda no
comportamento da rede.

## Quando usar

Quando a tarefa não cabe num turno de conversa: rodar uma bateria de testes,
executar uma mudança num repositório, produzir um texto longo. O agente
despacha, responde ao usuário que o trabalho começou, e consulta o estado nos
turnos seguintes.

Se a tarefa termina em segundos, não use isto: uma tool síncrona comum é mais
simples e devolve a resposta na hora.

## As duas tools

| Tool | O que faz | Devolve |
|---|---|---|
| `dispatch_job` | `POST /jobs` no serviço, cria o job | `{"status": "ok", "job_id": "..."}` |
| `get_job` | `GET /jobs/{id}`, consulta o estado | `{"status": "ok", "job": {...}}` |

`dispatch_job` aceita `task` e `job_type` (`coding` ou `text`), mais os
opcionais `repo_url`, `branch`, `max_agents` e `deadline_s`. O que você não
passar não é enviado, então os defaults do serviço continuam valendo.

## Configuração

Três variáveis de ambiente, nenhuma com valor no repositório:

```bash
ROUTER_URL=https://<host-do-servico>      # obrigatória
ROUTER_SECRET=<segredo>                   # obrigatória, vai no header x-router-secret
ROUTER_TIMEOUT_S=30                       # opcional, default 30
```

As duas primeiras são lidas a cada chamada, não no import, então um processo
que carrega o ambiente tarde funciona normalmente. Faltando qualquer uma, a
tool responde `not_configured` **sem** fazer requisição.

## Wiring

```python
from atendentepro import JOB_DISPATCH_TOOLS, create_standard_network

network = create_standard_network(
    templates_root="client_templates",
    client="meu_cliente",
    custom_tools={"answer": JOB_DISPATCH_TOOLS},
)
```

A chave de `custom_tools` é o agente que ganha as tools. Qualquer agente
tool-capable serve (`triage`, `flow`, `answer`, `confirmation`, `usage`).

Para dar só uma das duas a um agente, importe direto:

```python
from agents import function_tool
from atendentepro import get_job

network = create_standard_network(
    templates_root="client_templates",
    client="meu_cliente",
    custom_tools={"answer": [function_tool(get_job)]},
)
```

## Estados do job

`get_job` devolve o job como o serviço o mantém. O campo `job.status` passa por
`created`, `routed`, `awaiting_approval`, `running`, `judged`, e termina em
`done` ou `failed`.

Um job que terminou em `failed` **é uma consulta bem-sucedida**: o erro está em
`job.status`, e a tool responde `{"status": "ok", ...}`. Isso é proposital, o
agente precisa saber que o trabalho falhou para poder explicar ao usuário.

## Erros

Nenhuma das duas tools levanta exceção. Uma exceção dentro de um
`function_tool` derruba o turno do agente, o que transformaria uma queda
momentânea do serviço numa conversa quebrada. Em vez disso, o erro volta como
JSON para o agente ler:

| `error` | Quando | Campos extras |
|---|---|---|
| `not_configured` | Falta `ROUTER_URL` ou `ROUTER_SECRET` | |
| `invalid_request` | `job_type` inválido, ou 400/422 do serviço | `detail` do serviço |
| `unauthorized` | 401 ou 403 | |
| `not_found` | 404, job inexistente | |
| `unavailable` | 503, sem agente saudável | `retry_after` em segundos |
| `timeout` | O serviço não respondeu a tempo | |
| `unreachable` | Falha de transporte | |
| `bad_response` | 2xx com corpo que não é JSON | |

O segredo nunca aparece na resposta, nem no `detail`, nem no texto do erro de
transporte (só o tipo da exceção é reportado).

## Sem retry automático

As tools fazem **uma** requisição e reportam o que aconteceu. Não há laço de
retry interno, de propósito: cada despacho consome quota de assinatura no lado
do executor, então reenviar é decisão de quem chama, nunca um loop silencioso
da biblioteca.

Quando o serviço responde `unavailable`, ele informa em `retry_after` quantos
segundos esperar. Use esse valor para decidir, em vez de tentar de novo na
hora.
