# Exemplo: Custom Provider (APIs OpenAI-compatible)

Este exemplo demonstra como usar AtendentePro com diferentes providers de LLM alem do OpenAI e Azure, usando `provider="custom"`.

## Estrutura

```
custom_provider/
├── README.md                     # Esta documentacao
├── example_deepseek.py           # DeepSeek
├── example_gemini.py             # Google Gemini
├── example_grok.py               # xAI Grok
├── example_mistral.py            # Mistral AI
├── example_ollama.py             # Ollama (local)
├── example_vllm.py               # vLLM (local)
├── example_openrouter.py         # OpenRouter (multi-provider)
├── example_env_vars.py           # Configuracao via variaveis de ambiente
└── run_example.py                # Script para testar
```

## O que e provider="custom"?

O provider `custom` permite conectar AtendentePro a qualquer API que implemente o protocolo OpenAI Chat Completions. Basta fornecer a `base_url` e a `api_key` do provider.

| Parametro | Descricao |
|-----------|-----------|
| `provider` | Deve ser `"custom"` |
| `custom_base_url` | URL base da API (ex.: `https://api.deepseek.com/v1`) |
| `custom_api_key` | Chave de API do provider |
| `default_model` | Nome do modelo no provider (ex.: `deepseek-chat`) |

## Como funciona internamente

Quando `provider="custom"`:

1. AtendentePro cria um `AsyncOpenAI(api_key=..., base_url=...)` apontando para o endpoint custom
2. Configura o Agents SDK para usar este client via `set_default_openai_client()`
3. Forca o uso da API `chat_completions` (em vez de `responses`) via `set_default_openai_api("chat_completions")`
4. O Knowledge Agent automaticamente usa `client.chat.completions.create()` para RAG

Isso significa que **todos os agentes** (Triage, Flow, Interview, etc.) funcionam automaticamente com o provider custom, sem nenhuma configuracao adicional.

## Providers testados

| Provider | Base URL | Modelo exemplo | Observacao |
|----------|----------|----------------|------------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` | Otimo custo-beneficio |
| Google Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` | Endpoint OpenAI-compatible do Gemini |
| xAI Grok | `https://api.x.ai/v1` | `grok-3-latest` | |
| Mistral | `https://api.mistral.ai/v1` | `mistral-large-latest` | |
| Ollama | `http://localhost:11434/v1` | `llama3.1` | Roda local, sem custo |
| vLLM | `http://localhost:8000/v1` | `meta-llama/Llama-3.1-8B-Instruct` | Roda local com GPU |
| OpenRouter | `https://openrouter.ai/api/v1` | `anthropic/claude-sonnet-4` | Multi-provider gateway |

## Via variaveis de ambiente (.env)

```env
ATENDENTEPRO_LICENSE_KEY=ATP_seu-token
OPENAI_PROVIDER=custom
CUSTOM_BASE_URL=https://api.deepseek.com/v1
CUSTOM_API_KEY=sk-...
DEFAULT_MODEL=deepseek-chat
```

## Via codigo

```python
from atendentepro import activate, configure, create_standard_network
from pathlib import Path

activate("ATP_seu-token")

configure(
    provider="custom",
    custom_api_key="sk-...",
    custom_base_url="https://api.deepseek.com/v1",
    default_model="deepseek-chat",
)

network = create_standard_network(
    templates_root=Path("./config"),
    client="meu_cliente",
)
```

## Trocar de provider em runtime

```python
from atendentepro import configure

# Comecar com DeepSeek
configure(
    provider="custom",
    custom_api_key="sk-deep...",
    custom_base_url="https://api.deepseek.com/v1",
    default_model="deepseek-chat",
)

# ... usar a rede ...

# Trocar para OpenAI
configure(
    provider="openai",
    openai_api_key="sk-openai...",
    default_model="gpt-4o",
)

# O cache do client e limpo automaticamente ao chamar configure()
```

## Modelo por agente

Cada agente pode usar um modelo diferente. Combine com `agent_models`:

```python
network = create_standard_network(
    templates_root=Path("./config"),
    client="meu_cliente",
    agent_models={
        "triage": "deepseek-chat",         # modelo rapido para triagem
        "knowledge": "deepseek-reasoner",  # modelo avancado para RAG
    },
)
```

Agentes sem entrada em `agent_models` usam o `default_model` global.

## Embedding model

O modelo de embedding para RAG pode ser configurado:

```bash
EMBEDDING_MODEL=text-embedding-3-small
```

```python
configure(embedding_model="text-embedding-3-small")
```

> **Nota:** Providers que nao suportam embeddings (ex.: DeepSeek, Ollama sem embeddings) podem precisar de um provider separado para RAG, ou desabilitar o Knowledge Agent com embeddings.
> Veja `docs/examples/custom_embeddings/` para exemplos completos com Ollama, Gemini, Mistral, vLLM e OpenRouter.

## Executar exemplos

```bash
# Instalar dependencias
pip install atendentepro python-dotenv

# Configurar .env com as chaves do provider desejado
# Ver cada exemplo para as variaveis necessarias

# Executar
python docs/examples/custom_provider/run_example.py
```
