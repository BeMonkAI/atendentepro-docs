# Passo 28 (opcional): tools HTTP com a identidade do chamador

> **Code:** `atendentepro/service/tool_materializer.py` (`ToolSchema.http`),
> `atendentepro/models/context.py` (`ContextNote.user_context` / `tool_auth`).
> **Status:** opt-in (issue #548). Sem `http` no `ToolSchema` e sem `tool_auth`
> no `/chat`, o comportamento e o `config_hash` ficam byte-for-byte.

## O problema

As `tool_schemas` inline (#326) sao passthrough: devolvem
`pending_client_persist` e quem chamou refaz a chamada. O modelo nao ve o
resultado no mesmo turno, entao uma tool de LEITURA (status, lista) nao
funciona assim. MCP tem headers fixos por tenant. Nenhum dos dois caminhos
deixa a tool agir **como o usuario final da conversa**.

## O que muda

1. **Identidade no contexto da execucao.** `POST /chat` e `/chat/stream`
   aceitam `tool_auth` (a credencial do chamador, ex.: o bearer do usuario
   final). O servico coloca `user_context` e `tool_auth` no `ctx.context` do
   run (`ContextNote`). Os dois ficam FORA de serializacao e `repr`: nunca vao
   para o prompt, log, trace nem `config_hash`, e vivem so durante a request.
   Uma `function_tool` propria le `ctx.context.user_context`.
2. **Modo HTTP que executa.** Um `ToolSchema` com o bloco `http` faz UMA
   chamada HTTP e devolve a resposta ao modelo.

```json
{
  "name": "run_status",
  "description": "Status de uma rodada",
  "bound_agent": "answer",
  "parameters": {
    "type": "object",
    "properties": {"project_id": {"type": "string"}, "run_id": {"type": "string"}}
  },
  "http": {
    "method": "GET",
    "url_env": "MY_API_URL",
    "path": "/api/v1/projects/{project_id}/runs/{run_id}",
    "auth": "caller",
    "timeout_s": 10
  }
}
```

- **URL base so por env:** `url_env` nomeia a variavel, e o NOME precisa estar em
  `ATENDENTEPRO_TOOL_HTTP_URL_ENVS` (nega tudo por padrao, igual a allowlist de
  nomes). O valor precisa ser `http(s)://host`.
- **Caminho:** cada `{placeholder}` precisa ser um parametro da tool e e
  preenchido URL-encoded (`../` nao atravessa o caminho). Os demais argumentos
  nao nulos viram query string (GET) ou corpo JSON (POST).
- **`auth: caller`:** manda `Authorization: Bearer <tool_auth>`. Sem `tool_auth`
  na request, a tool **nao chama** e devolve `missing_caller_auth` ao modelo.
  `auth: none` nao manda header.
- **Resposta ao modelo:** `{"status": "ok" | "http_error", "code", "body"}`,
  cortada em 8000 caracteres; rede fora do ar vira
  `{"status": "error", "error": "http_unreachable"}`.
- **Log:** so nome da tool, status e latencia. Nunca o token.

## Env

| Variavel | Default | Para que |
|---|---|---|
| `ATENDENTEPRO_TOOL_NAME_ALLOWLIST` | vazio (nega tudo) | nomes de tool aceitos (#326, inalterado) |
| `ATENDENTEPRO_TOOL_HTTP_URL_ENVS` | vazio (nega tudo) | nomes das env vars que podem dar a URL base |
| a variavel apontada por `url_env` | — | URL base `http(s)://host` |

## Recorte v1

- So `GET` e `POST`, um request por chamada, sem retry.
- MCP continua com headers fixos. Header MCP por request fica para outra issue,
  porque a sessao MCP e compartilhada por rede.
