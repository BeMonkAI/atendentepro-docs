# Passo 2: Variáveis de ambiente

## Objetivo

Configurar as variáveis de ambiente necessárias para licença e API de linguagem (OpenAI ou Azure). O método recomendado é usar um arquivo `.env` na raiz do projeto.

## Onde configurar

- Arquivo `.env` na raiz do projeto (carregar com `python-dotenv` ou equivalente), ou
- Variáveis de ambiente do sistema / ambiente de execução

## Variáveis obrigatórias

| Variável | Descrição |
|----------|-----------|
| `ATENDENTEPRO_LICENSE_KEY` | Token de licença da biblioteca (obter em contato@monkai.com.br) |
| `OPENAI_API_KEY` | Chave da API OpenAI (ou usar variáveis Azure abaixo) |

## Variáveis opcionais

**Azure OpenAI:**

| Variável | Descrição |
|----------|-----------|
| `OPENAI_PROVIDER` | `azure` |
| `AZURE_API_KEY` | Chave do recurso Azure |
| `AZURE_API_ENDPOINT` | URL do recurso (ex.: https://seu-recurso.openai.azure.com) |
| `AZURE_API_VERSION` | Ex.: 2024-02-15-preview |
| `AZURE_DEPLOYMENT_NAME` | Nome do deployment (ex.: gpt-4o) |

**Custom Provider (API OpenAI-compatible):** DeepSeek, Gemini, Grok, Mistral, Ollama, vLLM, etc.

| Variável | Descrição |
|----------|-----------|
| `OPENAI_PROVIDER` | `custom` |
| `CUSTOM_BASE_URL` | URL base da API (ex.: https://api.deepseek.com/v1) |
| `CUSTOM_API_KEY` | Chave da API do provider |
| `DEFAULT_MODEL` | Nome do modelo (ex.: deepseek-chat, gemini-2.0-flash) |

**Memória (GRKMemory):** use apenas se instalou `atendentepro[memory]`

| Variável | Descrição |
|----------|-----------|
| `GRKMEMORY_API_KEY` | Token MonkAI para o GRKMemory |
| `GRKMEMORY_STORAGE_BACKEND` | Backend de armazenamento da memória: `file` (default, flat-file single-process) ou `postgres` (pgvector cross-process — remove o pin de instância única + volume persistente). Requer `grkmemory>=1.9.0` |
| `GRKMEMORY_POSTGRES_DSN` | DSN do Postgres — **obrigatório** quando `GRKMEMORY_STORAGE_BACKEND=postgres`. Requer `pip install atendentepro[memory-postgres]` |
| `GRKMEMORY_EMBEDDING_DIM` | Dimensão do índice vetorial externo (default `1536`) |

> O default permanece `file` — deploys existentes ficam inalterados até optar explicitamente por externalizar o armazenamento.

## Exemplo de arquivo .env

Crie ou atualize o arquivo `.env` na raiz do projeto com o conteúdo abaixo. Substitua os placeholders pelos valores reais. **Nunca commitar este arquivo com chaves reais.**

```env
# Obrigatório
ATENDENTEPRO_LICENSE_KEY=ATP_seu-token-aqui
OPENAI_API_KEY=sk-sua-chave-openai

# Opcional: Azure OpenAI (descomente e preencha se usar Azure)
# OPENAI_PROVIDER=azure
# AZURE_API_KEY=sua-chave-azure
# AZURE_API_ENDPOINT=https://seu-recurso.openai.azure.com
# AZURE_API_VERSION=2024-02-15-preview
# AZURE_DEPLOYMENT_NAME=gpt-4o

# Opcional: Custom Provider (descomente e preencha se usar DeepSeek, Gemini, etc.)
# OPENAI_PROVIDER=custom
# CUSTOM_BASE_URL=https://api.deepseek.com/v1
# CUSTOM_API_KEY=sk-...
# DEFAULT_MODEL=deepseek-chat

# Opcional: Memória (apenas se usar atendentepro[memory])
# GRKMEMORY_API_KEY=seu-token-grkmemory
```

Garanta que `.env` está no `.gitignore`:

```
.env
```

## Nota para o Copilot

Criar ou atualizar o arquivo `.env` com as chaves necessárias. Usar placeholders no exemplo e lembrar ao usuário de substituir por valores reais. Nunca commitar valores reais de tokens ou API keys; sempre usar variáveis de ambiente ou `.env` e manter `.env` no `.gitignore`.
