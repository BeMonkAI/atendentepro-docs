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

| Provider    | Modo                   | Env var esperada    | json_schema | tools | embeddings |
|-------------|------------------------|---------------------|-------------|-------|------------|
| `openai`    | SDK nativo             | `OPENAI_API_KEY`    | Sim         | Sim   | Sim        |
| `azure`     | SDK nativo             | `AZURE_API_KEY`     | Sim         | Sim   | Sim        |
| `anthropic` | **Adapter nativo**     | `ANTHROPIC_API_KEY` | Sim*        | Sim   | Nao        |
| `gemini`    | **Adapter nativo**     | `GEMINI_API_KEY`    | Sim         | Sim   | Sim        |
| `deepseek`  | OpenAI-compatible      | `DEEPSEEK_API_KEY`  | Nao         | Sim   | Nao        |

*\*Anthropic: json_schema via synthetic tool pattern*

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
