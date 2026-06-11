# Setup completo AtendentePro — para colar no Copilot

Siga o setup abaixo no projeto atual. Substitua os placeholders pelos valores reais. Aplique apenas os passos opcionais (memória, user_loader) se forem necessários para este projeto. Respeite a seção de cuidados ao final.

---

## 1. Instalação

```bash
pip install atendentepro
```

Opcionais (só se o projeto precisar):
- Memória de longo prazo: `pip install atendentepro[memory]`
- Tracing: `pip install atendentepro[tracing]`
- Tuning: `pip install atendentepro[tuning]`

---

## 2. Variáveis de ambiente (.env)

Criar arquivo `.env` na raiz do projeto. Garantir que `.env` está no `.gitignore`. Nunca commitar chaves reais.

```env
ATENDENTEPRO_LICENSE_KEY=[ATP_SEU_TOKEN]
OPENAI_API_KEY=[OPENAI_API_KEY]

# Opcional Azure (descomente se usar)
# OPENAI_PROVIDER=azure
# AZURE_API_KEY=...
# AZURE_API_ENDPOINT=...
# AZURE_API_VERSION=2024-02-15-preview
# AZURE_DEPLOYMENT_NAME=gpt-4o

# Opcional Custom Provider (DeepSeek, Gemini, Grok, Mistral, Ollama, etc.)
# OPENAI_PROVIDER=custom
# CUSTOM_BASE_URL=https://api.deepseek.com/v1
# CUSTOM_API_KEY=sk-...
# DEFAULT_MODEL=deepseek-chat

# Opcional memória (apenas se usar atendentepro[memory])
# GRKMEMORY_API_KEY=...
```

---

## 3. Ativação e criação da rede

No código de entrada, ativar antes de qualquer uso da rede e criar a rede:

```python
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from atendentepro import activate, create_standard_network
from agents import Runner

load_dotenv()
activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))

network = create_standard_network(
    templates_root=Path("[CAMINHO_PASTA_TEMPLATES]"),
    client="[NOME_CLIENTE]",
)

async def main():
    messages = [{"role": "user", "content": "Olá, preciso de ajuda"}]
    result = await Runner.run(network.triage, messages)
    print(result.final_output)

asyncio.run(main())
```

Substituir:
- `[CAMINHO_PASTA_TEMPLATES]`: pasta que contém a subpasta do cliente (ex.: `config` ou `templates`)
- `[NOME_CLIENTE]`: nome da subpasta (ex.: `meu_cliente` ou `standard`)

---

## 4. Estrutura de pastas e triage_config.yaml mínimo

Criar a pasta do cliente e o arquivo obrigatório. Exemplo: se `templates_root=config` e `client=meu_cliente`, criar `config/meu_cliente/triage_config.yaml`.

Conteúdo mínimo de `triage_config.yaml`:

```yaml
agent_keywords:
  flow_agent:
    keywords: ["fluxo", "processo", "opções", "menu"]
    description: "Fluxos e opções"
  knowledge_agent:
    keywords: ["conhecimento", "documentação", "dúvida", "informação"]
    description: "Base de conhecimento"
  answer_agent:
    keywords: ["resposta", "ajuda", "suporte"]
    description: "Respostas diretas"

routing_rules:
  priority_order:
    - "answer_agent"
    - "knowledge_agent"
    - "flow_agent"
  default_agent: "knowledge_agent"
```

---

## 5. Opcional: Memória de contexto longo

Aplicar apenas se o projeto precisar de memória (conversas anteriores).

- Instalar: `pip install atendentepro[memory]`
- Adicionar no .env: `GRKMEMORY_API_KEY=...`
- Código:

```python
from atendentepro.memory import run_with_memory, create_grk_backend

network.memory_backend = create_grk_backend()
# Em vez de Runner.run, usar:
result = await run_with_memory(network, network.triage, messages)
```

Em multi-usuário ou canal compartilhado, passar sempre `user_id` (e `session_id` se aplicável) em cada chamada a `run_with_memory`.

---

## 6. Opcional: User loader

Aplicar apenas se o projeto precisar carregar dados do usuário por request (banco, CSV, API).

- user_loader retorna `UserContext(user_id=..., role=..., metadata=...)` com dados do **request atual**.
- Não usar user_loader para memória nem session_id; session_id por parâmetro ou `network.session_id_factory`.

```python
from atendentepro.models import UserContext

def loader(messages):
    return UserContext(user_id="...", role="cliente", metadata={})

network = create_standard_network(..., user_loader=loader)
```

---

## 7. Principais cuidados (checklist)

- [ ] Não commitar `.env`; manter no `.gitignore`. Não colar chaves em código.
- [ ] Chamar `activate()` antes de qualquer uso da rede.
- [ ] Em multi-usuário ou canal compartilhado: sempre passar `user_id` (e `session_id` quando aplicável) em `run_with_memory`.
- [ ] user_loader: retornar dados do request atual; não usar para session_id.
- [ ] Não concatenar input do usuário em system prompts (ver docs/SECURITY.md ao estender).
- [ ] Pasta de templates deve existir e conter pelo menos `triage_config.yaml`; `templates_root` + `client` devem apontar para ela.

Referências: [docs/setup_passo_a_passo/07_cuidados_principais.md](07_cuidados_principais.md), [docs/SECURITY.md](../SECURITY.md).
