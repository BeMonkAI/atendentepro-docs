# Passo 25 (opcional): servidores MCP como fonte de tools

> **Code:** `atendentepro/mcp.py` + `mcp_config.yaml`.
> **Status:** opt-in (issue #491). Sem o arquivo (ou com lista vazia) o
> caminho atual fica byte-for-byte.

## O que e

O [Model Context Protocol](https://modelcontextprotocol.io/) expoe tools
de um servidor remoto. O OpenAI Agents SDK ja sabe consumir isso via
`Agent.mcp_servers`. Este passo e o fio declarativo da lib: o tenant
declara o servidor no YAML, a lib instancia, conecta no `/setup` (ou no
`/chat` stateless) e anexa so nos agentes listados.

Nao e um substituto de `custom_tools` / `tool_schemas`. MCP entra como
fonte extra de tools no agente; tools locais continuam no mesmo
`Agent.tools`.

## Recorte v1

- Transportes: `sse` e `streamable_http`. `stdio` / `command` sao
  rejeitados no parse (um template de tenant nao pode spawnar processo
  no host).
- URL e headers so via env: `url_env` e `header_env`. Literal `url:` no
  YAML e erro.
- `bound_agents` obrigatorio, lista nao vazia, so chaves tool-capable
  (`triage`, `flow`, `interview`, `answer`, `knowledge`, `confirmation`,
  `usage`, `scheduling`, `escalation`, `feedback`, `onboarding`).
  `farewell` e rejeitado.
- `allowed_tool_names` (opcional) vira o `ToolFilter` estatico do SDK.
- Um `MCPServer` por declaracao, compartilhado entre os agentes bound.
- Connect e fail-loud: URL/env/servidor ruim falha o `/setup` (ou o
  primeiro `/chat` inline). Sem fallback silencioso.
- `create_standard_network` continua sincrono. `await network.connect_mcp()`
  roda no `TenantManager.setup`, no `/chat` stateless e (para callers de
  biblioteca) em `AgentNetwork.run()`.
- Eviction do cache de rede e do tenant agenda `cleanup_mcp`.
- `config_hash` cobre a declaracao YAML, nao a lista descoberta em
  `list_tools`.

Fora do v1: `HostedMCPTool`, stdio supervisionado, websocket, bind por
`tools_for` de access-filter, reconnect com backoff.

## YAML

`client_templates/<cliente>/mcp_config.yaml`:

```yaml
mcp_servers:
  - name: crm
    transport: sse
    url_env: CRM_MCP_URL
    header_env:
      Authorization: CRM_MCP_TOKEN
    bound_agents: [knowledge, interview]
    allowed_tool_names: [search_account]
    cache_tools_list: true
```

`cache_tools_list` default e `true` (o SDK default e `false`; a lib
assume catalogo estavel no v1).

Env correspondente:

```bash
export CRM_MCP_URL="https://mcp.example/sse"
export CRM_MCP_TOKEN="Bearer ..."
```

No `/setup` ou no `config.yamls` do `/chat` inline, a chave e
`mcp_config` (mesmo padrao dos outros YAMLs). Sem o arquivo, nada muda.

## Callers de biblioteca

```python
network = create_standard_network(templates_root=..., client="meu_cliente")
await network.connect_mcp()  # ou use network.run(), que conecta sozinho
```

## Seguranca

- Nunca coloque URL, token ou header em YAML rastreado.
- Nao use `stdio` "so no dev" neste arquivo: o parser rejeita em qualquer
  ambiente.
- `bound_agents` e o access-filter de v1. Sem ele, o Knowledge Agent
  veria tools de um CRM que so o Interview deveria chamar.
