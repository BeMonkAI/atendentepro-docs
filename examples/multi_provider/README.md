# Multi-Provider — Exemplos de Uso

O AtendentePro suporta **múltiplos provedores de LLM** no mesmo sistema,
permitindo que cada agente use o modelo mais adequado ao seu papel.

## Conceito

```python
from atendentepro import ProviderConfig

# ProviderConfig resolve base_url e api_key automaticamente
# para provedores conhecidos: openai, deepseek, gemini, anthropic
pc = ProviderConfig(provider="deepseek", model="deepseek-reasoner")
```

## Provedores conhecidos (KNOWN_PROVIDERS)

| Provider     | Modo                   | Env var esperada      | json_schema | tools | embeddings |
|--------------|------------------------|-----------------------|-------------|-------|------------|
| `openai`     | SDK nativo             | `OPENAI_API_KEY`      | Sim         | Sim   | Sim        |
| `azure`      | SDK nativo             | `AZURE_API_KEY`       | Sim         | Sim   | Sim        |
| `anthropic`  | **Adapter nativo**     | `ANTHROPIC_API_KEY`   | Sim*        | Sim   | Nao        |
| `gemini`     | **Adapter nativo**     | `GEMINI_API_KEY`      | Sim         | Sim   | Sim        |
| `deepseek`   | OpenAI-compatible      | `DEEPSEEK_API_KEY`    | Nao         | Sim   | Nao        |
| `maritaca`   | OpenAI-compatible      | `MARITACA_API_KEY`    | Nao         | Sim   | Nao        |
| `zai`        | OpenAI-compatible      | `ZAI_API_KEY`         | Sim         | Sim   | Nao        |
| `xai`        | OpenAI-compatible      | `XAI_API_KEY`         | Nao         | Sim   | Nao        |
| `dashscope`  | OpenAI-compatible      | `DASHSCOPE_API_KEY`   | Sim         | Sim   | Sim        |
| `moonshot`   | OpenAI-compatible      | `MOONSHOT_API_KEY`    | Sim         | Sim   | Nao        |
| `openrouter` | OpenAI-compatible      | `OPENROUTER_API_KEY`  | Nao**       | Sim   | Nao        |
| `vllm`       | OpenAI-compatible      | `VLLM_API_KEY`        | Nao         | Sim   | Nao        |

*\*Anthropic: json_schema via synthetic tool pattern*

*\*\*OpenRouter e um agregador: o suporte a json_schema depende do MODELO
roteado, nao do provider. A flag fica conservadora (`Nao`) para manter o
fallback de parse manual, que funciona com qualquer modelo.*

`vllm` e self-hosted: nao tem endpoint default, o chamador passa `base_url`.
Os demais resolvem o endpoint por `KNOWN_PROVIDERS` quando `base_url` e `None`.

### Adapters nativos vs OpenAI-compatible

Providers com **adapter nativo** (`anthropic`, `gemini`) usam o SDK oficial do provider,
traduzindo automaticamente para a interface OpenAI. Vantagens:

- Suporte completo a function calling e handoffs
- Structured output (json_schema) funciona — guardrails ok
- Gemini: embeddings nativos — RAG funciona sem provider separado
- Melhor performance e compatibilidade que o modo OpenAI-compatible

```python
# Instalar adapters:
pip install atendentepro[anthropic]  # AnthropicAdapter
pip install atendentepro[gemini]     # GeminiAdapter
```

## Ordem de resolução

```
agent_providers (ProviderConfig → Model instance)
    ↓ fallback
agent_models (string → usa provider global)
    ↓ fallback
default_model (config global)
```

## Failover de provider (opt-in, #490)

Por default o turno usa um provider so. Se ele cair (timeout, 429, 5xx),
o atendimento para. `failover` em `provider_config.yaml` declara uma cadeia
de tentativa para o turno inteiro:

```yaml
failover:
  enabled: true
  chain:
    - {provider: openai, model: gpt-4.1}
    - {provider: azure, model: gpt-4.1}
  on_errors: [timeout, 5xx, 429]   # default (nao use a chave `on`: YAML 1.1 trata como bool)
  breaker_open_s: 30        # default
```

Regras do v1 (falha no load da config se quebradas):

- opt-in (`enabled: false` ou ausente = caminho atual, sem `run_config`)
- cadeia com no minimo 2 hops, cada um com `provider` + `model`
- todo hop tem que resolver dialect `gpt` (Gemini/Anthropic/Qwen ficam de fora)
- todo hop tem que ter o mesmo `json_schema` (openai+azure ok; openai+openrouter nao)
- 400/401/403 e erro de schema NAO trocam de hop
- `run_config=` do caller vence a cadeia
- breaker por provider, no processo; fail-open se o breaker falhar

Nao combine com `agent_providers` no v1: o `RunConfig` da cadeia vale para
o turno inteiro e sobrescreve o model por agente.

## MCP como fonte de tools (opt-in, #491)

Failover troca o *provider do turno*. MCP troca a *fonte de tools* de um
agente. Sao eixos diferentes e nao se misturam no v1.

`mcp_config.yaml` declara servidores remotos (`sse` ou `streamable_http`).
A lib instancia `MCPServerSse` / `MCPServerStreamableHttp` do Agents SDK
e anexa em `Agent.mcp_servers` so nos `bound_agents`. URL e headers vem
de env (`url_env` / `header_env`); `stdio` e rejeitado. Ver
[Passo 25](../../setup_passo_a_passo/25_opcionais_mcp.md).

## Exemplos

| Arquivo | Descrição |
|---|---|
| `example_single_provider.py` | Um único provider externo (DeepSeek) com modelos por agente |
| `example_multi_provider.py` | 4 providers simultâneos (OpenAI + DeepSeek + Gemini + Claude) |
| `example_cost_optimized.py` | Estratégia de otimização de custo por tiers |
| `example_hybrid.py` | Combina `agent_providers` + `agent_models` |
| `example_custom_provider.py` | Provider customizado (Ollama, vLLM, etc.) |
| `example_gemini_native.py` | Gemini nativo para agentes específicos (adapter) |
| `example_gemini_full.py` | 100% Gemini — todos os agentes com adapter nativo |

## Variáveis de ambiente

```bash
# .env
ATENDENTEPRO_LICENSE_KEY=ATP_seu-token

# Providers (defina apenas os que for usar)
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
```
