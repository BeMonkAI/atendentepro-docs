# Exemplo: Embedding Models Alternativos

Este exemplo demonstra como usar modelos de embedding que nao sejam da OpenAI no Knowledge Agent (RAG) do AtendentePro.

## Estrutura

```
custom_embeddings/
├── README.md                          # Esta documentacao
├── example_ollama_embeddings.py       # Ollama (local, sem custo)
├── example_gemini_embeddings.py       # Google Gemini
├── example_mistral_embeddings.py      # Mistral AI
├── example_vllm_embeddings.py         # vLLM (local com GPU)
├── example_openrouter_embeddings.py   # OpenRouter (gateway)
└── example_jina_embeddings.py         # Jina AI / OpenAI com modelo menor
```

## Como funciona

O AtendentePro usa o parametro `embedding_model` para definir qual modelo de embedding sera usado no Knowledge Agent (RAG). O embedding e gerado pelo **mesmo client** configurado no provider.

```python
configure(
    provider="custom",
    custom_base_url="...",
    custom_api_key="...",
    default_model="...",       # modelo para chat/agentes
    embedding_model="...",     # modelo para embeddings/RAG
)
```

Ou via variavel de ambiente:

```bash
EMBEDDING_MODEL=nomic-embed-text
```

## Tabela de modelos de embedding por provider

| Provider | Modelo | Dimensoes | Observacao |
|----------|--------|-----------|------------|
| **OpenAI** | `text-embedding-3-large` | 3072 | Padrao do AtendentePro |
| **OpenAI** | `text-embedding-3-small` | 1536 | Mais barato, boa qualidade |
| **OpenAI** | `text-embedding-ada-002` | 1536 | Legacy |
| **Ollama** | `nomic-embed-text` | 768 | Local, sem custo |
| **Ollama** | `mxbai-embed-large` | 1024 | Local, melhor qualidade |
| **Ollama** | `all-minilm` | 384 | Local, mais leve |
| **Ollama** | `snowflake-arctic-embed` | 1024 | Local |
| **Google Gemini** | `text-embedding-004` | 768 | Via endpoint OpenAI-compatible |
| **Mistral** | `mistral-embed` | 1024 | Multilingue |
| **vLLM** | `BAAI/bge-large-en-v1.5` | 1024 | Local com GPU |
| **vLLM** | `BAAI/bge-m3` | 1024 | Local, multilingue |
| **vLLM** | `intfloat/multilingual-e5-large` | 1024 | Local, multilingue |
| **OpenRouter** | `openai/text-embedding-3-small` | 1536 | Via gateway |

## Compatibilidade de embeddings

O modelo de embedding precisa ser compativel com os embeddings armazenados no arquivo `.pkl` do Knowledge Agent. Se voce trocar o modelo de embedding, **precisa regenerar os embeddings**.

### Exemplo: gerar embeddings com Ollama

```python
import pickle
from openai import OpenAI

client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")

documents = ["Texto do documento 1...", "Texto do documento 2..."]
embeddings = []

for doc in documents:
    response = client.embeddings.create(model="nomic-embed-text", input=doc)
    embeddings.append({
        "text": doc,
        "embedding": response.data[0].embedding,
    })

with open("embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)
```

### Exemplo: gerar embeddings com Mistral

```python
import pickle
from openai import OpenAI

client = OpenAI(
    api_key="sua-chave-mistral",
    base_url="https://api.mistral.ai/v1",
)

documents = ["Texto do documento 1...", "Texto do documento 2..."]
embeddings = []

for doc in documents:
    response = client.embeddings.create(model="mistral-embed", input=doc)
    embeddings.append({
        "text": doc,
        "embedding": response.data[0].embedding,
    })

with open("embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)
```

## Providers sem suporte a embeddings

Alguns providers de chat **nao oferecem embeddings**:

| Provider | Embedding? | Alternativa |
|----------|-----------|-------------|
| DeepSeek | Nao | Usar Ollama local ou OpenAI para embeddings |
| xAI Grok | Nao | Usar Ollama local ou OpenAI para embeddings |

Nestes casos, voce tem duas opcoes:

1. **Desabilitar RAG**: usar `include_knowledge=False` no `create_standard_network()`
2. **Provider hibrido**: usar o provider custom para chat, e gerar embeddings offline com outro provider

## Executar exemplos

```bash
pip install atendentepro python-dotenv

# Para Ollama (local):
ollama pull llama3.1
ollama pull nomic-embed-text
python docs/examples/custom_embeddings/example_ollama_embeddings.py

# Para Gemini:
# Configurar CUSTOM_API_KEY no .env
python docs/examples/custom_embeddings/example_gemini_embeddings.py

# Para Mistral:
# Configurar CUSTOM_API_KEY no .env
python docs/examples/custom_embeddings/example_mistral_embeddings.py
```
