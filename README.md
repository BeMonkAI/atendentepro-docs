# AtendentePro — Public Documentation & Examples

> Public mirror of documentation and examples for [AtendentePro](https://pypi.org/project/atendentepro/) — v0.41.0.
> Source library lives at [BeMonkAI/atendentepro](https://github.com/BeMonkAI/atendentepro) (private).

## For humans

- [Setup guide](setup_passo_a_passo/) — step-by-step install & first network
- [Feature examples](examples/) — concept-driven examples by feature
- [Runner scripts](run/) — provider-neutral end-to-end scripts

## For AI assistants

- **`llms.txt`** — short index ([llmstxt.org](https://llmstxt.org) convention)
- **`llms-full.txt`** — entire bundle concatenated; ideal for LLM context

Quick paste into your AI of choice:

```bash
curl -sL https://raw.githubusercontent.com/BeMonkAI/atendentepro-docs/main/llms-full.txt | pbcopy
```

## Versioning

Each release of `atendentepro` on PyPI has a matching tag in this repo
(e.g. PyPI `0.21.0` ↔ git tag `v0.21.0`). The `main` branch tracks
the latest released version.

---

# Library README (verbatim)

# AtendentePro

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/atendentepro.svg)](https://pypi.org/project/atendentepro/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

**Framework de orquestração de agentes IA para interações complexas**

Plataforma que unifica múltiplos agentes especializados para resolver demandas que envolvem diferentes fontes de dados, sistemas e fluxos de decisão — tudo orquestrado em um único lugar. Baseado no [OpenAI Agents SDK](https://github.com/openai/openai-agents-python).

### Principais Capacidades

| Capacidade | Descrição |
|------------|-----------|
| **Classificação Inteligente** | Identifica a intenção e direciona para o agente especializado |
| **Integração de Dados** | Conecta documentos (RAG), CSVs, bancos de dados SQL e APIs externas |
| **Orquestração de Fluxos** | Handoffs automáticos entre agentes conforme a complexidade da demanda |
| **Tom e Estilo Customizáveis** | AgentStyle para personalizar linguagem, tom e formato de respostas |
| **Escalonamento Controlado** | Transferência para atendimento humano com contexto preservado |
| **Gestão de Feedbacks** | Sistema de tickets para reclamações, sugestões e acompanhamento |
| **Configuração Declarativa** | Personalização completa via arquivos YAML |
| **Tuning (Post-Training)** | Melhoria dos YAMLs com base em feedback e conversas (módulo opcional) |
| **Memória de contexto longo** | GRKMemory para buscar e injetar memórias e persistir turnos (módulo opcional) |
| **Servidor Multi-Tenant** | API REST para gerenciar redes de agentes por tenant via HTTP (módulo opcional) |
| **Multi-Provider** | Suporte a OpenAI, Azure OpenAI e qualquer API OpenAI-compatible (DeepSeek, Gemini, Grok, Mistral, Ollama, vLLM, etc.) |

---

## 📚 Documentação e Exemplos

Toda a documentação prática (setup passo a passo, exemplos por feature, runner scripts) está espelhada em um repositório público:

**👉 [github.com/BeMonkAI/atendentepro-docs](https://github.com/BeMonkAI/atendentepro-docs)**

Para passar tudo de uma vez para um assistente de IA (Claude, ChatGPT, Cursor):

```bash
curl -sL https://raw.githubusercontent.com/BeMonkAI/atendentepro-docs/main/llms-full.txt | pbcopy
```

O arquivo `llms-full.txt` segue a convenção [llmstxt.org](https://llmstxt.org) — todas as docs concatenadas em um único markdown otimizado para contexto de LLM. Cada release no PyPI tem uma tag matching no repo de docs (ex: `atendentepro==0.21.0` ↔ `git tag v0.21.0`).

---

## 📋 Índice

- [Documentação e Exemplos](#-documentação-e-exemplos)
- [Instalação](#-instalação)
- [Ativação (Licença)](#-ativação-licença)
- [Configurar Provider (OpenAI / Azure / Custom)](#-configurar-provider-openai--azure--custom)
- [Início Rápido](#-início-rápido)
- [CLI (Agent Builder)](#️-cli-agent-builder)
- [Arquitetura](#-arquitetura)
- [Agentes Disponíveis](#-agentes-disponíveis)
- [Servidor Multi-Tenant (atendentepro.service)](#-servidor-multi-tenant-atendenteproservice)
- [Criar Templates Customizados](#-criar-templates-customizados)
- [Configurações YAML](#-configurações-yaml)
- [Escalation Agent](#-escalation-agent)
- [Feedback Agent](#-feedback-agent)
- [Fluxo de Handoffs](#-fluxo-de-handoffs)
- [Estilo de Comunicação](#-estilo-de-comunicação-agentstyle)
- [Single Reply Mode](#-single-reply-mode)
- [Filtros de Acesso](#-filtros-de-acesso-roleuser)
- [Carregamento de Usuários](#-carregamento-de-usuários-user-loader)
- [Múltiplos Agentes](#-múltiplos-agentes-multi-interview--knowledge)
- [Tracing e Monitoramento](#-tracing-e-monitoramento)
- [Tuning (Post-Training)](#-tuning-post-training)
- [Memória de contexto longo (GRKMemory)](#-memória-de-contexto-longo-grkmemory)
- [Segurança em Produção](#segurança-em-produção)
- [Suporte](#-suporte)

---

## 📦 Instalação

```bash
# Via PyPI
pip install atendentepro

# Com monitoramento (recomendado)
pip install atendentepro[tracing]

# Com servidor multi-tenant (FastAPI)
pip install atendentepro[server]
```

---

## 🔑 Ativação (Licença)

A biblioteca **requer um token de licença** para funcionar.

### Opção 1: Variável de Ambiente (Recomendado)

```bash
export ATENDENTEPRO_LICENSE_KEY="ATP_seu-token-aqui"
```

### Opção 2: Via Código

```python
from atendentepro import activate

activate("ATP_seu-token-aqui")
```

### Opção 3: Arquivo .env

```env
ATENDENTEPRO_LICENSE_KEY=ATP_seu-token-aqui
OPENAI_API_KEY=sk-sua-chave-openai
```

### Obter um Token

Entre em contato para obter seu token:
- 📧 **Email:** contato@monkai.com.br
- 🌐 **Site:** https://www.monkai.com.br

---

## 🔐 Configurar Provider (OpenAI / Azure / Custom)

AtendentePro suporta 3 providers: **OpenAI** (padrão), **Azure OpenAI** e **Custom** (qualquer API OpenAI-compatible).

### OpenAI (padrão)

```bash
# .env
OPENAI_API_KEY=sk-sua-chave-openai
```

```python
from atendentepro import configure
configure(openai_api_key="sk-sua-chave-openai", default_model="gpt-4.1")
```

### Azure OpenAI

```bash
# .env
OPENAI_PROVIDER=azure
AZURE_API_KEY=sua-chave-azure
AZURE_API_ENDPOINT=https://seu-recurso.openai.azure.com
AZURE_API_VERSION=2024-02-15-preview
AZURE_DEPLOYMENT_NAME=gpt-4o
```

### Custom Provider (DeepSeek, Gemini, Grok, Mistral, Ollama, vLLM, etc.)

Use `provider="custom"` para conectar a qualquer API OpenAI-compatible via `base_url` customizada.

**Via .env:**

```bash
# .env
OPENAI_PROVIDER=custom
CUSTOM_BASE_URL=https://api.deepseek.com/v1
CUSTOM_API_KEY=sk-sua-chave
DEFAULT_MODEL=deepseek-chat
```

**Via codigo:**

```python
from atendentepro import activate, configure

activate("ATP_seu-token")

# DeepSeek
configure(
    provider="custom",
    custom_api_key="sk-...",
    custom_base_url="https://api.deepseek.com/v1",
    default_model="deepseek-chat",
)

# Gemini (OpenAI-compatible endpoint)
configure(
    provider="custom",
    custom_api_key="sua-chave-gemini",
    custom_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    default_model="gemini-2.0-flash",
)

# Grok (xAI)
configure(
    provider="custom",
    custom_api_key="xai-...",
    custom_base_url="https://api.x.ai/v1",
    default_model="grok-3-latest",
)

# Ollama (local)
configure(
    provider="custom",
    custom_api_key="ollama",
    custom_base_url="http://localhost:11434/v1",
    default_model="llama3.1",
)
```

**Providers testados:**

| Provider | `custom_base_url` | Modelo exemplo |
|----------|-------------------|----------------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Google Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` |
| xAI Grok | `https://api.x.ai/v1` | `grok-3-latest` |
| Mistral | `https://api.mistral.ai/v1` | `mistral-large-latest` |
| Ollama | `http://localhost:11434/v1` | `llama3.1` |
| vLLM | `http://localhost:8000/v1` | `meta-llama/Llama-3.1-8B-Instruct` |
| OpenRouter | `https://openrouter.ai/api/v1` | `anthropic/claude-sonnet-4` |

### Modelo por agente

Cada agente pode usar um modelo diferente. Use `agent_models` para definir modelos específicos:

```python
network = create_standard_network(
    templates_root=Path("./config"),
    client="meu_cliente",
    agent_models={
        "triage": "gpt-4.1-mini",      # modelo rápido para triagem
        "knowledge": "gpt-4.1",         # modelo completo para RAG
        "flow": "gpt-4.1-mini",
    },
)
```

Agentes sem entrada em `agent_models` usam o `default_model` global (padrão: `gpt-4.1`).

### Embedding model

O modelo de embedding para RAG pode ser configurado via variável de ambiente ou código:

```bash
EMBEDDING_MODEL=text-embedding-3-large
```

```python
configure(embedding_model="text-embedding-3-large")
```

---

## ⚡ Início Rápido

```python
import asyncio
from pathlib import Path
from atendentepro import activate, create_standard_network
from agents import Runner

# 1. Ativar
activate("ATP_seu-token")

async def main():
    # 2. Criar rede de agentes
    network = create_standard_network(
        templates_root=Path("./meu_cliente"),
        client="config"
    )
    
    # 3. Executar conversa
    result = await Runner.run(
        network.triage,
        [{"role": "user", "content": "Olá, preciso de ajuda"}]
    )
    
    print(result.final_output)

asyncio.run(main())
```

---

## 🛠️ CLI (Agent Builder)

CLI machine-friendly para criar, validar, testar e fazer deploy de configurações de agentes — pensada para ser usada por agentes de IA (Claude Code, Cursor, etc.) e em pipelines de automação. Toda saída é JSON em `stdout`, erros em `stderr`, exit code reflete sucesso/falha.

### Instalação

A CLI é instalada por padrão com o pacote:

```bash
pip install atendentepro
```

### Comandos

| Comando | Descrição |
|---|---|
| `list` | Lista templates de clientes existentes |
| `init <client>` | Cria um novo template de cliente (a partir de YAML, JSON inline ou base) |
| `validate <client>` | Valida a configuração YAML de um cliente |
| `test <client> <message>` | Envia uma mensagem de teste para a rede de agentes |
| `deploy <client>` | Faz deploy do cliente para um servidor multi-tenant |

### Exemplos

```bash
# Listar clientes existentes
atendentepro list --templates-root ./client_templates

# Criar novo cliente a partir de YAML unificado
atendentepro init meu_cliente --from-yaml ./meu_cliente.yaml

# Validar configuração
atendentepro validate meu_cliente --templates-root ./client_templates

# Testar com mensagem (OpenAI)
export ATENDENTEPRO_LICENSE_KEY="ATP_seu-token"
export OPENAI_API_KEY="sk-..."
atendentepro test meu_cliente "Olá, preciso de ajuda" \
  --templates-root ./client_templates

# Deploy para servidor multi-tenant
atendentepro deploy meu_cliente \
  --server http://localhost:8000 \
  --tenant-id meu_cliente
```

### Configurar Provider no `test`

O comando `test` aceita os 3 providers suportados pelo AtendentePro:

| Flag | Env var | Provider |
|---|---|---|
| `--provider openai` | `OPENAI_API_KEY` | OpenAI (default) |
| `--provider azure` | `AZURE_API_KEY` | Azure OpenAI |
| `--provider custom` | — | Qualquer API OpenAI-compatible (DeepSeek, Gemini, Grok, Mistral, Ollama, vLLM) |
| `--api-key` | — | API key do provider selecionado |
| `--license-key` | `ATENDENTEPRO_LICENSE_KEY` | Licença AtendentePro |
| `--model` | — | Nome do modelo (default: `gpt-4.1-mini`) |

```bash
# OpenAI
atendentepro test meu_cliente "olá" --provider openai --model gpt-4.1-mini

# Azure OpenAI
atendentepro test meu_cliente "olá" \
  --provider azure \
  --api-key <azure-key> \
  --model gpt-4o

# Custom (ex: DeepSeek)
atendentepro test meu_cliente "olá" \
  --provider custom \
  --api-key sk-deepseek-... \
  --model deepseek-chat
```

### Exit codes

| Code | Significado |
|---|---|
| `0` | Sucesso |
| `1` | Falha (validação, API, deploy, etc.) |

---

## 🏗️ Arquitetura

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              ATENDENTEPRO                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   👤 Usuário                                                               │
│       │                                                                    │
│       ▼                                                                    │
│   ┌─────────────┐                                                         │
│   │   Triage    │──► Classifica intenção do usuário                       │
│   └─────────────┘                                                         │
│         │                                                                  │
│    ┌────┴────┬─────────┬─────────┬─────────┬─────────┬─────────┐          │
│    ▼         ▼         ▼         ▼         ▼         ▼         ▼          │
│ ┌──────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐     │
│ │ Flow │ │Knowl. │ │Confirm│ │ Usage │ │Onboard│ │Escala.│ │Feedbk.│     │
│ └──────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘     │
│                                          * Onboard desabilitado por padrão │
│    │                                                                       │
│    ▼                                                                       │
│ ┌─────────────┐                                                           │
│ │  Interview  │──► Coleta informações estruturadas                        │
│ └─────────────┘                                                           │
│       │                                                                    │
│       ▼                                                                    │
│ ┌─────────────┐                                                           │
│ │   Answer    │──► Sintetiza resposta final                               │
│ └─────────────┘                                                           │
│                                                                            │
│ ══════════════════════════════════════════════════════════════════════    │
│  📞 Escalation → Transfere para atendimento humano IMEDIATO               │
│  📝 Feedback   → Registra tickets para resposta POSTERIOR                 │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agentes Disponíveis

| Agente | Descrição | Quando Usar |
|--------|-----------|-------------|
| **Triage** | Classifica intenção e direciona | Sempre (ponto de entrada) |
| **Flow** | Apresenta opções/menu ao usuário | Múltiplas opções disponíveis |
| **Interview** | Coleta informações através de perguntas | Precisa de dados do usuário |
| **Answer** | Sintetiza resposta final | Após coletar informações |
| **Knowledge** | Consulta RAG e dados estruturados | Perguntas sobre documentos/dados |
| **Confirmation** | Valida com respostas sim/não | Confirmar ações |
| **Usage** | Responde dúvidas sobre o sistema | "Como funciona?" |
| **Onboarding** | Cadastro de novos usuários | Novos usuários |
| **Escalation** | Transfere para humano | Urgente/não resolvido |
| **Feedback** | Registra tickets | Dúvidas/reclamações/sugestões |

---

## 🌐 Servidor Multi-Tenant (atendentepro.service)

O modulo `atendentepro.service` fornece um servidor FastAPI que gerencia redes de agentes por tenant via API REST. Permite que qualquer aplicacao (Edge Function, backend, WhatsApp bot) configure e converse com agentes sem escrever codigo Python.

### Instalacao

```bash
pip install atendentepro[server]
```

### Uso rapido

```bash
export OPENAI_API_KEY="sk-..."
export ATENDENTEPRO_LICENSE_KEY="ATP_..."
export ATENDENTEPRO_LICENSE_SECRET="..."

atendentepro-service
```

### Endpoints

| Endpoint | Descricao |
|---|---|
| `GET /health` | Status do servidor e tenants carregados |
| `POST /setup` | Configura tenant enviando YAMLs de configuracao |
| `POST /chat` | Envia mensagem e recebe resposta do agente |

### Exemplo: Configurar e conversar

```bash
# 1. Configurar um tenant
curl -X POST http://localhost:8000/setup \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "meu_tenant", "yamls": {"triage_config": "agent_name: Triage\nkeywords: ..."}}'

# 2. Configurar com agentes customizados e handoffs
curl -X POST http://localhost:8000/setup \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "meu_tenant",
    "yamls": {"triage_config": "..."},
    "include_agents": {"onboarding": true, "feedback": false},
    "network_config": {"triage": ["knowledge", "flow"], "knowledge": ["triage"]}
  }'

# 3. Enviar mensagem com contexto de usuario (RBAC)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "meu_tenant",
    "session_id": "s1",
    "message": "Ola!",
    "user_context": {"user_id": "u1", "role": "admin"}
  }'
```

### Customizacao

| Feature | Via API (JSON) | Via codigo (Python) |
|---|---|---|
| Agent inclusion (on/off) | `include_agents` em `/setup` | `default_include_agents` |
| Custom handoffs | `network_config` em `/setup` | `default_network_config` |
| Custom tools | -- | `custom_tools` / `default_custom_tools` |
| User context (RBAC) | `user_context` em `/chat` | `default_user_loader` |
| Styles, guardrails, etc. | Via YAML no campo `yamls` | -- |

### Deploy via Docker

```bash
docker build -f Dockerfile.service -t atendentepro-service .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY="sk-..." \
  -e ATENDENTEPRO_LICENSE_KEY="ATP_..." \
  -e ATENDENTEPRO_LICENSE_SECRET="..." \
  atendentepro-service
```

**Documentacao completa:** [atendentepro/service/README.md](atendentepro/service/README.md)

---

## 📁 Criar Templates Customizados

### Estrutura de Pastas

```
meu_cliente/
├── triage_config.yaml       # ✅ Obrigatório
├── flow_config.yaml         # Recomendado
├── interview_config.yaml    # Recomendado
├── answer_config.yaml       # Opcional
├── knowledge_config.yaml    # Opcional
├── escalation_config.yaml   # Recomendado
├── feedback_config.yaml     # Recomendado
├── guardrails_config.yaml   # Recomendado
├── style_config.yaml        # Opcional - Tom e estilo
└── data/                    # Dados estruturados (CSV, etc.)
```

### Usar o Template

```python
from pathlib import Path
from atendentepro import create_standard_network

network = create_standard_network(
    templates_root=Path("./"),
    client="meu_cliente",
    include_escalation=True,
    include_feedback=True,
)
```

---

## ⚙️ Configurações YAML

### triage_config.yaml (Obrigatório)

Define palavras-chave para classificação e (opcionalmente) regras adicionais de roteamento:

```yaml
agent_name: "Triage Agent"

# Palavras-chave por agente. Cada lista vira hint não-determinístico para o LLM.
keywords:
  flow:        ["produto", "serviço", "preço"]
  knowledge:   ["documentação", "manual", "como funciona"]
  # 👇 Bloco DETERMINÍSTICO: basta popular `escalation` para a lib gerar
  # um "ROTEAMENTO DE ESCALONAMENTO" no prompt — o Triage transfere
  # imediatamente para o Escalation Agent quando qualquer gatilho aparecer.
  escalation:  ["falar com humano", "urgência", "emergência"]

# (Opcional) Pistas de roteamento — NÃO-determinístico, apenas instrui o LLM.
routing_rules:
  priority_order: [knowledge, flow]
  default_agent: onboarding   # fallback quando a intenção do usuário não fica clara
  # (Opcional, issue #246) Lista de agentes que geram um bloco DETERMINÍSTICO
  # extra (## Roteamento de <agente> (DETERMINÍSTICO)). Cada agente listado
  # deve ter `keywords.<agente>` configurado. `escalation` continua auto-firando
  # mesmo quando ausente da lista, preservando compat com configs antigas.
  deterministic_agents: [onboarding, knowledge]

# (Opcional, issue #247) Texto livre PREPENDADO antes do prompt base do Triage.
# Como entra ANTES do prompt base, tem peso maior que o suffix — use para
# overrides de comportamento que precisam vencer regras do prompt default.
custom_prompt_prefix: |
  ## REGRAS DE ROTEAMENTO PRIORITARIAS
  - Saudações simples sem intenção clara → onboarding IMEDIATAMENTE.
  - Pedidos de diagnóstico médico → escalation IMEDIATAMENTE.

# (Opcional, issue #226) Texto livre APPENDADO ao prompt final do Triage,
# depois de keywords + bloco de escalation + routing_rules. Use para
# adicionar regras de roteamento condicionais sem precisar de deploy.
custom_prompt_suffix: |
  ## Regras adicionais
  - Quando o usuário pergunta "vocês fazem X?", encaminhe para knowledge.
  - Quando o usuário pede diagnóstico médico, encaminhe para escalation.

# (Opcional) Substitui o prompt inteiro do Triage. Equivalente ao kwarg Python
# `triage_custom_instructions`. Quando setado, `keywords` e `routing_rules`
# NÃO são injetados — embuta tudo no texto.
# custom_prompt: |
#   Você é o Triage Agent do meu_cliente. ...
```

**Quando usar cada coisa**:

| Recurso | Tipo | Quando usar |
|---|---|---|
| `keywords.<agente>` | Hint não-determinístico | Roteamento normal por intenção |
| `keywords.escalation` | **Bloco determinístico (auto)** | Forçar handoff imediato p/ Escalation (legado #88) |
| `routing_rules.deterministic_agents` | **Blocos determinísticos genéricos** | Forçar handoff imediato para qualquer agente listado (issue #246) |
| `routing_rules.default_agent` | Hint não-determinístico | Fallback para mensagens ambíguas (ex: "oi") |
| `routing_rules.priority_order` | Hint não-determinístico | Desempate entre agentes quando 2+ casam |
| `custom_prompt_prefix` | Texto livre prependado (peso forte) | Overrides prioritários que precisam vencer o prompt base |
| `custom_prompt_suffix` | Texto livre appendado (peso fraco) | Regras condicionais extras sem redeploy |
| `custom_prompt` | Substitui prompt inteiro | Reescrever Triage do zero |

> ⚠️ Chaves de topo não reconhecidas (typos, blocos antigos) são logadas como `WARNING` — o YAML não falha silenciosamente (issue #225). Vale para `triage_config.yaml`, `interview_config.yaml`, `confirmation_config.yaml`, `scheduling_config.yaml`, `style_config.yaml` e `knowledge_config.yaml`.

### flow_config.yaml

Define opções/menu:

```yaml
agent_name: "Flow Agent"

topics:
  - id: 1
    label: "Vendas"
    keywords: ["comprar", "preço", "orçamento"]
    
  - id: 2
    label: "Suporte"
    keywords: ["problema", "erro", "ajuda"]
    
  - id: 3
    label: "Financeiro"
    keywords: ["pagamento", "boleto", "fatura"]
```

### answer_config.yaml (Opcional)

Define o template de resposta final do Answer Agent:

```yaml
agent_name: "Answer Agent"

answer_template: |
  Com base nas informações coletadas, prepare uma resposta clara e objetiva.
  Inclua um resumo do que foi solicitado e os próximos passos.
```

### interview_config.yaml

Define perguntas para coleta:

```yaml
agent_name: "Interview Agent"

interview_questions: |
  Para cada tópico, faça as seguintes perguntas:
  
  ## Vendas
  1. Qual produto você tem interesse?
  2. Qual quantidade desejada?
  3. Qual seu email para contato?
  
  ## Suporte
  1. Descreva o problema
  2. Quando começou?
  3. Já tentou alguma solução?
```

### guardrails_config.yaml

Define escopo e restrições:

```yaml
agent_scopes:
  triage_agent:
    about: |
      Este assistente pode ajudar com:
      - Informações sobre produtos
      - Suporte técnico
      - Dúvidas sobre serviços
  flow_agent:
    about: |
      Apresenta opções de produtos e serviços disponíveis.

out_of_scope_message:
  default: |
    Desculpe, não posso ajudar com esse assunto.
    Posso ajudar com produtos, suporte ou serviços.
  triage_agent: |
    Essa pergunta está fora do escopo do nosso atendimento.
```

---

## 📞 Escalation Agent

Transfere para atendimento humano quando:
- Usuário solicita explicitamente
- Tópico não coberto pelo sistema
- Usuário demonstra frustração
- Agente não consegue resolver

### escalation_config.yaml

```yaml
name: "Escalation Agent"

triggers:
  explicit_request:
    - "quero falar com um humano"
    - "atendente humano"
    - "falar com uma pessoa"
  
  frustration:
    - "você não está me ajudando"
    - "isso não resolve"

channels:
  phone:
    enabled: true
    number: "0800-123-4567"
    hours: "Seg-Sex 8h-18h"
  
  email:
    enabled: true
    address: "atendimento@empresa.com"
    sla: "Resposta em até 24h"
  
  whatsapp:
    enabled: true
    number: "(11) 99999-9999"

business_hours:
  start: 8
  end: 18
  days: [monday, tuesday, wednesday, thursday, friday]

messages:
  greeting: "Entendo que você precisa de um atendimento especializado."
  out_of_hours: "Nosso atendimento funciona de Seg-Sex, 8h-18h."
```

### Usar Escalation

```python
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    include_escalation=True,
    escalation_channels="""
📞 Telefone: 0800-123-4567 (Seg-Sex 8h-18h)
📧 Email: atendimento@empresa.com
💬 WhatsApp: (11) 99999-9999
""",
)
```

---

## 📝 Feedback Agent

Registra tickets para:
- ❓ **Dúvidas** - Perguntas que precisam de pesquisa
- 💬 **Feedback** - Opinião sobre produto/serviço
- 📢 **Reclamação** - Insatisfação formal (prioridade alta)
- 💡 **Sugestão** - Ideia de melhoria
- ⭐ **Elogio** - Agradecimento
- ⚠️ **Problema** - Bug/erro técnico (prioridade alta)

### feedback_config.yaml

```yaml
name: "Feedback Agent"

protocol_prefix: "TKT"  # Formato: TKT-20240106-ABC123

ticket_types:
  - name: "duvida"
    label: "Dúvida"
    default_priority: "normal"
    
  - name: "reclamacao"
    label: "Reclamação"
    default_priority: "alta"
    
  - name: "sugestao"
    label: "Sugestão"
    default_priority: "baixa"

email:
  enabled: true
  brand_color: "#660099"
  brand_name: "Minha Empresa"
  sla_message: "Retornaremos em até 24h úteis."

priorities:
  - name: "baixa"
    sla_hours: 72
  - name: "normal"
    sla_hours: 24
  - name: "alta"
    sla_hours: 8
  - name: "urgente"
    sla_hours: 2
```

### Usar Feedback

As configurações (tipos de ticket, prefixo de protocolo, email, etc.) são **carregadas automaticamente** do `feedback_config.yaml` do template. Os tickets são persistidos em arquivo JSON (caminho configurável via `FEEDBACK_STORAGE_PATH`).

```python
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    include_feedback=True,
    # Opcional: sobrescrever configs do YAML via parâmetros
    # feedback_protocol_prefix="TKT",
    # feedback_brand_color="#660099",
    # feedback_brand_name="Minha Empresa",
)
```

### Diferença: Escalation vs Feedback

| Aspecto | Escalation | Feedback |
|---------|------------|----------|
| **Propósito** | Atendimento IMEDIATO | Registro para DEPOIS |
| **Urgência** | Alta | Pode aguardar |
| **Canal** | Telefone, chat | Email, ticket |
| **Protocolo** | ESC-XXXXXX | TKT-XXXXXX |
| **Quando usar** | "Quero falar com alguém" | "Tenho uma sugestão" |

---

## 🔄 Fluxo de Handoffs

```
Triage ──────► Flow, Knowledge, Confirmation, Usage, Onboarding*, Escalation, Feedback
Flow ────────► Interview, Triage, Escalation, Feedback
Interview ──► Answer, Escalation, Feedback
Answer ─────► Triage, Escalation, Feedback
Knowledge ──► Triage, Escalation, Feedback
Confirmation► Triage
Escalation ─► Triage, Feedback
Feedback ───► Triage, Escalation

* Onboarding desabilitado por padrão (include_onboarding=False)
```

### Configuração de Agentes

Você pode escolher exatamente quais agentes incluir na sua rede:

```python
from pathlib import Path
from atendentepro import create_standard_network

# Todos os agentes habilitados (padrão)
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
)

# Sem Knowledge Agent (para clientes sem base de conhecimento)
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    include_knowledge=False,
)

# Rede mínima (apenas fluxo principal)
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    include_knowledge=False,
    include_confirmation=False,
    include_usage=False,
    include_escalation=False,
    include_feedback=False,
)

# Apenas captura de leads (sem Knowledge nem Usage)
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    include_knowledge=False,
    include_usage=False,
)
```

### Parâmetros Disponíveis

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `include_flow` | `True` | Agente de fluxo conversacional |
| `include_interview` | `True` | Agente de entrevista/coleta |
| `include_answer` | `True` | Agente de resposta final |
| `include_knowledge` | `True` | Agente de base de conhecimento |
| `include_confirmation` | `True` | Agente de confirmação |
| `include_usage` | `True` | Agente de instruções de uso |
| `include_onboarding` | `False` | Agente de boas-vindas |
| `include_escalation` | `True` | Agente de escalonamento humano |
| `include_feedback` | `True` | Agente de tickets/feedback |
| `user_loader` | `None` | Função para carregar dados do usuário (User Loader) |
| `auto_load_user` | `False` | Carregar usuário automaticamente no início da sessão |
| `load_style_from_template` | `True` | Mesclar `style_config.yaml` do cliente com `global_style` / `agent_styles` (código sobrescreve YAML) |
| `triage_custom_instructions` | `None` | Substituir o corpo default do prompt do Triage (ver docstring de `create_standard_network`) |

---

## 🎨 Estilo de Comunicação (AgentStyle)

Personalize o tom e estilo de resposta dos agentes:

### Via Código

```python
from pathlib import Path
from atendentepro import create_standard_network, AgentStyle

# Estilo global (aplicado a todos os agentes)
global_style = AgentStyle(
    tone="profissional e consultivo",
    language_style="formal",      # formal, informal, neutro
    response_length="moderado",   # conciso, moderado, detalhado
    custom_rules="Sempre cumprimente o usuário pelo nome.",
)

# Estilos específicos por agente
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    global_style=global_style,
    agent_styles={
        "escalation": AgentStyle(
            tone="empático e acolhedor",
            custom_rules="Demonstre compreensão pela situação.",
        ),
        "knowledge": AgentStyle(
            tone="didático e paciente",
            response_length="detalhado",
        ),
    },
)
```

### Via YAML (style_config.yaml)

Por padrão, `create_standard_network()` carrega e aplica `<cliente>/style_config.yaml` quando o arquivo existe (`load_style_from_template=True`). Valores passados em `global_style` ou `agent_styles` no código têm precedência sobre o YAML.

```yaml
# Estilo Global
global:
  tone: "profissional e cordial"
  language_style: "formal"
  response_length: "moderado"
  custom_rules: |
    - Seja objetivo e claro nas respostas
    - Use linguagem inclusiva

# Estilos por Agente
agents:
  escalation:
    tone: "empático e tranquilizador"
    custom_rules: |
      - Demonstre compreensão pela situação
      - Assegure que o problema será resolvido

  knowledge:
    tone: "didático e paciente"
    response_length: "detalhado"
    custom_rules: |
      - Explique conceitos de forma acessível
      - Cite as fontes das informações

  feedback:
    tone: "solícito e atencioso"
    custom_rules: |
      - Agradeça o feedback recebido
      - Confirme o registro da solicitação
```

### Opções Disponíveis

| Parâmetro | Valores | Descrição |
|-----------|---------|-----------|
| `tone` | Texto livre | Tom da conversa (ex: "profissional", "empático") |
| `language_style` | `formal`, `informal`, `neutro` | Nível de formalidade |
| `response_length` | `conciso`, `moderado`, `detalhado` | Tamanho das respostas |
| `custom_rules` | Texto livre | Regras personalizadas |

---

## 🔧 Dependências

- Python 3.10+
- openai-agents >= 0.3.3
- openai >= 1.107.1
- pydantic >= 2.0.0
- PyYAML >= 6.0
- python-dotenv >= 1.0.0

---

## 📄 Variáveis de Ambiente

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| `ATENDENTEPRO_LICENSE_KEY` | Token de licença | ✅ Sim |
| `OPENAI_API_KEY` | Chave API OpenAI | ✅ (se OpenAI) |
| `OPENAI_PROVIDER` | `openai`, `azure` ou `custom` | Não |
| `DEFAULT_MODEL` | Modelo padrão; padrão: `gpt-4.1` | Não |
| `EMBEDDING_MODEL` | Modelo de embedding para RAG; padrão: `text-embedding-3-large` | Não |
| `AZURE_API_KEY` | Chave API Azure | ✅ (se Azure) |
| `AZURE_API_ENDPOINT` | Endpoint Azure (alias: `AZURE_OPENAI_ENDPOINT`) | ✅ (se Azure) |
| `AZURE_API_VERSION` | Versão da API Azure (alias: `AZURE_OPENAI_API_VERSION`) | Não |
| `AZURE_DEPLOYMENT_NAME` | Nome do deployment Azure | Não |
| `CUSTOM_BASE_URL` | URL base do provider custom (ex: `https://api.deepseek.com/v1`) | ✅ (se Custom) |
| `CUSTOM_API_KEY` | Chave API do provider custom | ✅ (se Custom) |
| `OCR_ENABLED` | Habilitar OCR; padrão: `true` | Não |
| `AZURE_AI_VISION_ENDPOINT` | Endpoint Azure AI Vision (para OCR) | Para OCR |
| `AZURE_AI_VISION_KEY` | Chave Azure AI Vision (para OCR) | Para OCR |
| `APPLICATION_INSIGHTS_CONNECTION_STRING` | Connection string do Application Insights (Azure) | Para tracing Azure |
| `MONKAI_TRACER_TOKEN` | Token do MonkAI Trace | Para tracing MonkAI |
| `CONTEXT_OUTPUT_DIR` | Diretório de saída de contexto; padrão: `context` | Não |
| `SMTP_HOST` | Servidor SMTP | Para emails |
| `SMTP_USER` | Usuário SMTP | Para emails |
| `SMTP_PASSWORD` | Senha SMTP | Para emails |
| `FEEDBACK_STORAGE_PATH` | Caminho do arquivo JSON de tickets | Persistência do Feedback Agent |
| `ATENDENTEPRO_ESCALATION_STORAGE` | Caminho do arquivo de escalation | Persistência do Escalation Agent |
| `ESCALATION_WEBHOOK_URL` | URL do webhook de escalation | Não |
| `ESCALATION_WEBHOOK_SECRET` | Secret para assinar webhooks de escalation | Não |
| `ESCALATION_HOUR_START` | Hora de início do horário comercial (escalation) | Não |
| `ESCALATION_HOUR_END` | Hora de fim do horário comercial (escalation) | Não |
| `GRKMEMORY_API_KEY` | Chave API do GRKMemory | Para memória |
| `ATENDENTEPRO_MEMORY_MAX_CHARS` | Máximo de caracteres de memória injetados; padrão: `8000` | Não |
| `SUPABASE_URL` | URL do Supabase (para tuning) | Para tuning |
| `SUPABASE_SERVICE_KEY` | Service key do Supabase (alias: `SUPABASE_ANON_KEY`) | Para tuning |
| `ATENDENTEPRO_PRODUCTION` | `1`/`true`/`yes`: validação online obrigatória; exige `ATENDENTEPRO_VALIDATION_URL` | Produção |
| `ATENDENTEPRO_VALIDATION_URL` | URL do endpoint de validação de licença (obrigatória em produção) | Produção |
| `ATENDENTEPRO_REQUIRE_USER_CONTEXT` | `1`/`true`/`yes`: exige `user_context` quando há filtros de acesso | Produção |
| `ATENDENTEPRO_REQUIRE_GUARDRAILS` | `1`/`true`/`yes`: log ERROR se guardrails do Triage não configurados | Produção |
| `ATENDENTEPRO_LOG_FORMAT` | `json` para logs estruturados JSON; padrão: `text` | Não |
| `ATENDENTEPRO_LOG_LEVEL` | Nível de log (DEBUG, INFO, WARNING, ERROR); padrão: `INFO` | Não |
| `ATENDENTEPRO_GUARDRAIL_CACHE_TTL` | TTL do cache de guardrails em segundos; padrão: `300` | Não |
| `ATENDENTEPRO_AGENT_TIMEOUT` | Timeout do agente em segundos (service); padrão: `60` | Não |
| `ATENDENTEPRO_RATE_LIMIT_MAX` | Máximo de requisições por janela (service); padrão: `100` | Não |
| `ATENDENTEPRO_RATE_LIMIT_WINDOW` | Janela do rate limit em segundos (service); padrão: `60` | Não |
| `ATENDENTEPRO_CORS_ORIGINS` | Origens CORS permitidas, separadas por vírgula (service) | Não |
| `PROXY_TRUSTED_IPS` | Lista CSV de IPs de proxies confiáveis para `X-Forwarded-For` (servidor) | Não |
| `ATENDENTEPRO_SESSION_TTL` | TTL de sessoes inativas em segundos (service); padrao: `3600` | Não |
| `HOST` | Host de escuta do service; padrao: `0.0.0.0` | Não |
| `PORT` | Porta de escuta do service; padrao: `8000` | Não |

### Segurança em Produção

Para uso em grande corporação, recomenda-se:

1. **Licença:** `ATENDENTEPRO_PRODUCTION=1` e `ATENDENTEPRO_VALIDATION_URL` configurada; segredo apenas no servidor de validação.
2. **Acesso:** `user_context` (ou `user_loader`) sempre fornecido ao criar a rede quando há filtros; opcionalmente `ATENDENTEPRO_REQUIRE_USER_CONTEXT=1`.
3. **Guardrails:** `guardrails_config.yaml` com escopo e blocklist; opcionalmente `ATENDENTEPRO_REQUIRE_GUARDRAILS=1`.
4. **Secrets:** API keys, SMTP etc. apenas em variáveis de ambiente ou vault; não logar config/env com segredos; logs de conteúdo em DEBUG apenas.

Ver [docs/PRODUCTION_SECURITY.md](docs/PRODUCTION_SECURITY.md) para checklist completo e variáveis.

---

## 🔁 Single Reply Mode

O **Single Reply Mode** permite configurar agentes para responderem apenas uma vez e automaticamente transferirem de volta para o Triage. Isso evita que a conversa fique "presa" em um agente específico.

📂 **Exemplos completos**: [docs/examples/single_reply/](docs/examples/single_reply/)

### Quando Usar

| Cenário | Recomendação |
|---------|--------------|
| **Chatbots de alto volume** | ✅ Ativar para respostas rápidas |
| **FAQ simples** | ✅ Knowledge com single_reply |
| **Coleta de dados** | ❌ Interview precisa múltiplas interações |
| **Onboarding** | ❌ Precisa guiar o usuário em etapas |
| **Confirmações** | ✅ Confirma e volta ao Triage |

### Exemplo 1: FAQ Bot (Via Código)

Chatbot otimizado para perguntas frequentes:

```python
from pathlib import Path
from atendentepro import create_standard_network

# FAQ Bot: Knowledge e Answer respondem uma vez
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    global_single_reply=False,
    single_reply_agents={
        "knowledge": True,  # FAQ: responde e volta
        "answer": True,     # Perguntas gerais: responde e volta
        "flow": True,       # Menu: apresenta e volta
    },
)
```

### Exemplo 2: Bot de Leads (Via Código)

Bot que coleta dados mas responde dúvidas rapidamente:

```python
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    global_single_reply=False,
    single_reply_agents={
        # Interview PRECISA de múltiplas interações para coletar dados
        "interview": False,
        
        # Outros agentes podem ser rápidos
        "knowledge": True,    # Tira dúvidas sobre produto
        "answer": True,       # Responde perguntas
        "confirmation": True, # Confirma cadastro
    },
)
```

### Exemplo 3: Ativar para TODOS os agentes

```python
network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    global_single_reply=True,  # Todos respondem uma vez
)
```

### Via YAML (single_reply_config.yaml)

Crie o arquivo `single_reply_config.yaml` na pasta do cliente:

```yaml
# Global: se true, TODOS os agentes respondem apenas uma vez
global: false

# Configuração por agente (sobrescreve global)
agents:
  # Agentes de consulta: respondem uma vez
  knowledge: true      # FAQ: responde e volta
  answer: true         # Perguntas: responde e volta
  confirmation: true   # Confirma e volta
  usage: true          # Explica uso e volta
  
  # Agentes de coleta: múltiplas interações
  interview: false     # Precisa coletar dados
  onboarding: false    # Precisa guiar usuário
  
  # Opcionais
  flow: true           # Menu: apresenta e volta
  escalation: true     # Registra e volta
  feedback: true       # Coleta feedback e volta
```

### Fluxo Visual

**Com single_reply=True:**

```
[Usuário: "Qual o preço?"]
         ↓
    [Triage] → detecta consulta
         ↓
  [Knowledge] → responde: "R$ 99,90"
         ↓
    [Triage] ← retorno AUTOMÁTICO
         ↓
[Usuário: "E a entrega?"]
         ↓
    [Triage] → nova análise (ciclo reinicia)
```

**Com single_reply=False (padrão):**

```
[Usuário: "Qual o preço?"]
         ↓
    [Triage] → detecta consulta
         ↓
  [Knowledge] → responde: "R$ 99,90"
         ↓
[Usuário: "E a entrega?"]
         ↓
  [Knowledge] → continua no mesmo agente
         ↓
[Usuário: "Quero falar com humano"]
         ↓
  [Knowledge] → handoff para Escalation
```

### Configuração Recomendada

Para a maioria dos casos de uso:

```yaml
global: false

agents:
  knowledge: true      # FAQ
  answer: true         # Perguntas gerais
  confirmation: true   # Confirmações
  
  interview: false     # Coleta de dados
  onboarding: false    # Guia de usuário
```

---

## 🔐 Filtros de Acesso (Role/User)

O sistema de **Filtros de Acesso** permite controlar quais agentes, prompts e tools estão disponíveis para cada usuário ou role (função).

📂 **Exemplos completos**: [docs/examples/access_filters/](docs/examples/access_filters/)

### Quando Usar

| Cenário | Solução |
|---------|---------|
| **Multi-tenant** | Diferentes clientes veem diferentes agentes |
| **Níveis de acesso** | Admin vê mais opções que cliente |
| **Segurança** | Dados sensíveis só para roles específicas |
| **Personalização** | Diferentes instruções por departamento |

### Níveis de Filtragem

1. **Agentes**: Habilitar/desabilitar agentes inteiros
2. **Prompts**: Adicionar seções condicionais aos prompts
3. **Tools**: Habilitar/desabilitar tools específicas

### Exemplo 1: Filtros de Agente (Via Código)

```python
from pathlib import Path
from atendentepro import (
    create_standard_network,
    UserContext,
    AccessFilter,
)

# Usuário com role de vendedor
user = UserContext(user_id="vendedor_123", role="vendedor")

# Filtros de agente
agent_filters = {
    # Feedback só para admin
    "feedback": AccessFilter(allowed_roles=["admin"]),
    # Escalation para todos exceto clientes
    "escalation": AccessFilter(denied_roles=["cliente"]),
}

network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    user_context=user,
    agent_filters=agent_filters,
)
```

### Exemplo 2: Prompts Condicionais

Adicione instruções específicas baseadas na role:

```python
from atendentepro import FilteredPromptSection

conditional_prompts = {
    "knowledge": [
        # Seção para vendedores
        FilteredPromptSection(
            content="\\n## Descontos\\nVocê pode oferecer até 15% de desconto.",
            filter=AccessFilter(allowed_roles=["vendedor"]),
        ),
        # Seção para admin
        FilteredPromptSection(
            content="\\n## Admin\\nVocê tem acesso total ao sistema.",
            filter=AccessFilter(allowed_roles=["admin"]),
        ),
    ],
}

network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    user_context=user,
    conditional_prompts=conditional_prompts,
)
```

### Exemplo 3: Tools Filtradas

```python
from atendentepro import FilteredTool
from agents import function_tool

@function_tool
def deletar_cliente(cliente_id: str) -> str:
    """Remove um cliente do sistema."""
    return f"Cliente {cliente_id} removido"

filtered_tools = {
    "knowledge": [
        FilteredTool(
            tool=deletar_cliente,
            filter=AccessFilter(allowed_roles=["admin"]),  # Só admin
        ),
    ],
}

network = create_standard_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    user_context=user,
    filtered_tools=filtered_tools,
)
```

### Via YAML (access_config.yaml)

```yaml
# Filtros de agente
agent_filters:
  feedback:
    allowed_roles: ["admin"]
  escalation:
    denied_roles: ["cliente"]

# Prompts condicionais
conditional_prompts:
  knowledge:
    - content: |
        ## Capacidades de Vendedor
        Você pode oferecer até 15% de desconto.
      filter:
        allowed_roles: ["vendedor"]

# Acesso a tools
tool_access:
  deletar_cliente:
    allowed_roles: ["admin"]
```

### Tipos de Filtro

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `allowed_roles` | Whitelist de roles | `["admin", "gerente"]` |
| `denied_roles` | Blacklist de roles | `["cliente"]` |
| `allowed_users` | Whitelist de usuários | `["user_vip_1"]` |
| `denied_users` | Blacklist de usuários | `["user_bloqueado"]` |

### Prioridade de Avaliação

1. `denied_users` - Se usuário está negado, **bloqueia**
2. `allowed_users` - Se lista existe e usuário está nela, **permite**
3. `denied_roles` - Se role está negada, **bloqueia**
4. `allowed_roles` - Se lista existe e role não está nela, **bloqueia**
5. **Permite por padrão** - Se nenhum filtro matched

### Fluxo Visual

```
┌────────────────────────────────────────────────┐
│         Requisição: role="vendedor"            │
└────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────┐
│              FILTRO DE AGENTES                 │
│  Knowledge: ✅ (vendedor allowed)              │
│  Escalation: ✅ (vendedor not denied)          │
│  Feedback: ❌ (only admin)                     │
└────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────┐
│             FILTRO DE PROMPTS                  │
│  Knowledge recebe: "## Descontos..."           │
│  (seção condicional para vendedor)             │
└────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────┐
│              FILTRO DE TOOLS                   │
│  consultar_comissao: ✅                        │
│  deletar_cliente: ❌ (only admin)              │
└────────────────────────────────────────────────┘
```

---

## 👤 Carregamento de Usuários (User Loader)

O **User Loader** carrega **dados do usuário** que ficam em uma estrutura de banco de dados (ou CSV/API): identidade, perfil, role e dados estatísticos daquele usuário. Não é para memória nem para sessão (conversa) — memória e session_id usam outros mecanismos (session_id_factory, parâmetros, backend de memória).

O carregamento pode ser usado **apenas para um agente**: chame `run_with_user_context(network, network.flow, messages)` (ou o agente desejado, ex.: flow) só para esse agente; os demais podem ser executados com `Runner.run(agent, messages)` sem user_loader.

O **user_loader deve retornar um UserContext com `user_id` preenchido** (obrigatório quando o loader retorna contexto). O **user_id deve vir de um único lugar (UserContext)** — ao usar user_loader, não informe user_id em dois lugares; quando houver user_loader, `run_with_memory` usará `loaded_user_context.user_id` e não deve ser passado um `user_id` diferente por parâmetro.

A função de carregamento (load_user / loader_func) busca os dados e **retorna um dicionário**. Esse dicionário preenche o UserContext: `user_id` e `role` vão para os campos fixos; o resto fica em **metadata**. Exemplo de acesso após o carregamento: `network.loaded_user_context.metadata.get("nome")`, `metadata.get("plano")`.

📂 **Exemplos completos**: [docs/examples/user_loader/](docs/examples/user_loader/)

🔧 **Padrão para campos custom do cliente** (`empresa`, `aad_object_id`, etc.): [docs/client_context_patterns.md](docs/client_context_patterns.md) — quando criar uma subclasse de `UserContext` para tipar campos específicos do diretório corporativo.

### Quando Usar

| Cenário | Solução |
|---------|---------|
| **Usuário existente** | Identifica automaticamente e pula onboarding |
| **Personalização** | Carrega dados do usuário (perfil, plano, etc.) do banco para respostas personalizadas |
| **Contexto enriquecido** | Agentes que usam run_with_user_context têm acesso a loaded_user_context (dados em banco/perfil) |
| **Múltiplas fontes** | Suporta CSV, banco de dados, APIs REST, etc. |

### Funcionalidades

1. **Extração automática** de identificadores (telefone, email, CPF, etc.)
2. **Carregamento de dados** de múltiplas fontes
3. **Criação automática** de `UserContext`
4. **Integração transparente** com a rede de agentes

### Exemplo 1: Carregamento de CSV

```python
from pathlib import Path
from atendentepro import (
    create_standard_network,
    create_user_loader,
    load_user_from_csv,
    extract_email_from_messages,
    run_with_user_context,
)

# Função para carregar do CSV
def load_user(identifier: str):
    return load_user_from_csv(
        csv_path=Path("users.csv"),
        identifier_field="email",
        identifier_value=identifier
    )

# Criar loader
loader = create_user_loader(
    loader_func=load_user,
    identifier_extractor=extract_email_from_messages
)

# Criar network com loader
network = create_standard_network(
    templates_root=Path("./templates"),
    user_loader=loader,
    include_onboarding=True,
)

# Executar com carregamento automático
messages = [{"role": "user", "content": "Meu email é joao@example.com"}]
result = await run_with_user_context(network, network.triage, messages)

# Verificar se usuário foi carregado
if network.loaded_user_context:
    print(f"Usuário: {network.loaded_user_context.metadata.get('nome')}")
```

### Exemplo 2: Carregamento de Banco de Dados

```python
import sqlite3
from atendentepro import create_user_loader, extract_email_from_messages

def load_from_db(identifier: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (identifier,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "role": row[1],
            "nome": row[2],
            "email": row[3],
        }
    return None

loader = create_user_loader(load_from_db, extract_email_from_messages)

network = create_standard_network(
    templates_root=Path("./templates"),
    user_loader=loader,
)
```

### Exemplo 3: Múltiplos Identificadores

```python
from atendentepro import (
    create_user_loader,
    extract_email_from_messages,
    extract_phone_from_messages,
)

def extract_identifier(messages):
    # Tenta email primeiro
    email = extract_email_from_messages(messages)
    if email:
        return email
    
    # Se não encontrou, tenta telefone
    phone = extract_phone_from_messages(messages)
    if phone:
        return phone
    
    return None

loader = create_user_loader(
    loader_func=load_user,
    identifier_extractor=extract_identifier
)
```

### Funções Disponíveis

#### Extratores de Identificador

```python
from atendentepro import (
    extract_phone_from_messages,    # Extrai telefone
    extract_email_from_messages,     # Extrai email
    extract_user_id_from_messages,  # Extrai CPF/user_id
)
```

#### Criar Loader

```python
from atendentepro import create_user_loader

loader = create_user_loader(
    loader_func=load_user_function,
    identifier_extractor=extract_email_from_messages  # Opcional
)
```

#### Executar com Contexto

```python
from atendentepro import run_with_user_context

result = await run_with_user_context(
    network,
    network.triage,
    messages
)
```

### Integração com Onboarding

Quando um `user_loader` está configurado:

- ✅ **Usuário encontrado**: Vai direto para o triage, sem passar pelo onboarding
- ✅ **Usuário não encontrado**: É direcionado para o onboarding normalmente
- ✅ **Contexto disponível**: Todos os agentes têm acesso a `network.loaded_user_context`

### Benefícios

1. ✅ **Experiência personalizada** - Respostas baseadas em dados do usuário
2. ✅ **Menos fricção** - Usuários conhecidos não precisam fazer onboarding
3. ✅ **Contexto rico** - Todos os agentes têm acesso a informações do usuário
4. ✅ **Flexível** - Suporta múltiplas fontes de dados
5. ✅ **Automático** - Funciona transparentemente durante a conversa

---

## 🔀 Múltiplos Agentes (Multi Interview + Knowledge)

O AtendentePro suporta criar **múltiplas instâncias** de Interview e Knowledge agents, cada um especializado em um domínio diferente.

📂 **Exemplo completo**: [docs/examples/multi_agents/](docs/examples/multi_agents/)

### Caso de Uso

Empresa que atende diferentes tipos de clientes:
- **Pessoa Física (PF)**: Produtos de consumo
- **Pessoa Jurídica (PJ)**: Soluções empresariais

### Arquitetura

```
                    ┌─────────────────┐
                    │     Triage      │
                    │  (entry point)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  Interview  │  │  Interview  │  │    Flow     │
    │     PF      │  │     PJ      │  │   (comum)   │
    └──────┬──────┘  └──────┬──────┘  └─────────────┘
           │                │
           ▼                ▼
    ┌─────────────┐  ┌─────────────┐
    │  Knowledge  │  │  Knowledge  │
    │     PF      │  │     PJ      │
    └─────────────┘  └─────────────┘
```

### Implementação

```python
from atendentepro import (
    create_custom_network,
    create_triage_agent,
    create_interview_agent,
    create_knowledge_agent,
)

# 1. Criar agentes especializados
interview_pf = create_interview_agent(
    interview_questions="CPF, data de nascimento, renda mensal",
    name="interview_pf",  # Nome único!
)

interview_pj = create_interview_agent(
    interview_questions="CNPJ, razão social, faturamento",
    name="interview_pj",  # Nome único!
)

knowledge_pf = create_knowledge_agent(
    knowledge_about="Produtos para consumidor final",
    name="knowledge_pf",
    single_reply=True,
)

knowledge_pj = create_knowledge_agent(
    knowledge_about="Soluções empresariais B2B",
    name="knowledge_pj",
    single_reply=True,
)

# 2. Criar Triage
triage = create_triage_agent(
    keywords_text="PF: CPF, pessoal, minha conta | PJ: CNPJ, empresa, MEI",
    name="triage_agent",
)

# 3. Configurar handoffs
triage.handoffs = [interview_pf, interview_pj, knowledge_pf, knowledge_pj]
interview_pf.handoffs = [knowledge_pf, triage]
interview_pj.handoffs = [knowledge_pj, triage]
knowledge_pf.handoffs = [triage]
knowledge_pj.handoffs = [triage]

# 4. Criar network customizada
network = create_custom_network(
    templates_root=Path("./meu_cliente"),
    client="config",
    network_config={
        "triage": ["interview_pf", "interview_pj", "knowledge_pf", "knowledge_pj"],
        "interview_pf": ["knowledge_pf", "triage"],
        "interview_pj": ["knowledge_pj", "triage"],
        "knowledge_pf": ["triage"],
        "knowledge_pj": ["triage"],
    },
)
```

### Cenários de Roteamento

| Mensagem do Usuário | Rota |
|---------------------|------|
| "Quero abrir conta para mim" | Triage → Interview PF → Knowledge PF |
| "Preciso de maquininha para minha loja" | Triage → Interview PJ → Knowledge PJ |
| "Quanto custa o cartão gold?" | Triage → Knowledge PF (direto) |
| "Capital de giro para empresa" | Triage → Knowledge PJ (direto) |

### Padrão: 1 Interview → 2 Knowledge

Outro padrão comum é ter um único Interview que pode direcionar para múltiplos Knowledge:

```
        ┌───────────────┐
        │   Interview   │
        │ (coleta dados)│
        └───────┬───────┘
                │
        ┌───────┴───────┐
        ▼               ▼
┌───────────────┐ ┌───────────────┐
│   Knowledge   │ │   Knowledge   │
│   Produtos    │ │Troubleshooting│
└───────────────┘ └───────────────┘
```

```python
# Um interview que direciona para múltiplos knowledge
interview.handoffs = [knowledge_produtos, knowledge_troubleshooting, triage]
```

📂 **Exemplo completo**: [example_one_interview_two_knowledge.py](docs/examples/multi_agents/example_one_interview_two_knowledge.py)

### Dicas

1. **Nomes únicos**: Cada agente precisa de um `name` distinto
2. **Handoffs claros**: Configure quais agentes cada um pode chamar
3. **Keywords no Triage**: Inclua palavras-chave para direcionar corretamente
4. **single_reply**: Use em Knowledge para evitar loops

---

## 📊 Tracing e Monitoramento

### MonkAI Trace (Recomendado)

Integração com [MonkAI Trace](https://github.com/BeMonkAI/monkai-trace) para monitoramento completo de agentes:

```bash
pip install monkai-trace
```

```python
from atendentepro import (
    activate,
    create_standard_network,
    configure_monkai_trace,
    run_with_monkai_tracking,
)

# 1. Ativar biblioteca
activate("ATP_seu-token")

# 2. Configurar MonkAI Trace
configure_monkai_trace(
    tracer_token="tk_seu_token_monkai",  # ou env MONKAI_TRACER_TOKEN
    namespace="meu-projeto",
)

# 3. Criar rede
network = create_standard_network(...)

# 4. Executar com tracking
result = await run_with_monkai_tracking(
    agent=network.triage,
    user_input="Olá, preciso de ajuda",
    user_id="user123",  # Opcional: para sessões multi-usuário
)
```

**Recursos do MonkAI Trace:**
- ✅ Tracking automático de sessões
- ✅ Segmentação de tokens (input, output, process, memory)
- ✅ Rastreamento de handoffs entre agentes
- ✅ Captura de ferramentas internas (web_search, RAG)
- ✅ Suporte multi-usuário (WhatsApp, chat)

### Uso Avançado

```python
from atendentepro import (
    get_monkai_hooks,
    set_monkai_user,
    set_monkai_input,
)
from agents import Runner

# Para controle manual
hooks = get_monkai_hooks()
set_monkai_user("5511999999999")  # WhatsApp
set_monkai_input("Como cancelar?")

result = await Runner.run(network.triage, messages, hooks=hooks)
```

### Application Insights (Azure)

Para Azure, use Application Insights:

```python
from atendentepro import configure_application_insights

configure_application_insights(
    connection_string="InstrumentationKey=..."
)
```

---

## 🔧 Tuning (Post-Training)

O módulo opcional **Tuning** usa feedback das conversas (Supabase) e registros do MonkAI Trace para sugerir melhorias nos YAMLs do cliente. As alterações são gravadas numa pasta de sugeridos (`client/_suggested/`) para revisão; o usuário decide se substitui os originais.

**Instalação:** `pip install atendentepro[tuning]`

**Variáveis de ambiente:** `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (ou `SUPABASE_ANON_KEY`), `MONKAI_TRACER_TOKEN`

**Fluxo resumido:**
1. Rodar o pipeline com `apply=True` e `write_to_suggested_folder=True` — os YAMLs alterados são gravados em `client/_suggested/` e um relatório `_suggestions_report.json` é gerado; os originais não são alterados.
2. Revisar os arquivos em `client/_suggested/` e o relatório.
3. Se aprovar, chamar `replace_originals_with_suggested(client, templates_root)` para copiar os sugeridos sobre os originais.

```python
from pathlib import Path
from atendentepro.tuning import run_tuning_pipeline, replace_originals_with_suggested

result = run_tuning_pipeline(
    namespace="customer-support",
    client="meu_cliente",
    templates_root=Path("./client_templates"),
    start_date="2025-01-01",
    apply=True,
    write_to_suggested_folder=True,
)
# Revisar client_templates/meu_cliente/_suggested/
replace_originals_with_suggested(client="meu_cliente", templates_root=Path("./client_templates"))
```

**Documentação completa:** [atendentepro/tuning/README.md](atendentepro/tuning/README.md) e [docs/TUNING.md](docs/TUNING.md)

---

## Memória de contexto longo (GRKMemory)

O módulo opcional **Memória** integra o [GRKMemory](https://pypi.org/project/grkmemory/) para memória de longo prazo: antes de cada execução do agente, busca memórias relevantes e injeta no contexto; após a resposta, persiste o turno. Suporte async e multi-tenant (`user_id` / `session_id`).

**Instalação:** `pip install atendentepro[memory]`

**Variáveis de ambiente:** `GRKMEMORY_API_KEY`, `OPENAI_API_KEY` (ou Azure conforme documentação do GRKMemory)

```python
from atendentepro import create_standard_network
from atendentepro.memory import run_with_memory, create_grk_backend

network = create_standard_network(templates_root=Path("templates"), client="standard")
network.memory_backend = create_grk_backend()

messages = [{"role": "user", "content": "O que combinamos na última vez?"}]
result = await run_with_memory(network, network.triage, messages)
```

Ao usar memória ou sessão, **user_id é obrigatório** (para isolar conversas por usuário). Toda sessão deve ter um **user_id** associado. Quando houver user_loader, use o mesmo user_id do UserContext — não informe em dois lugares; `run_with_memory` usará `loaded_user_context.user_id` automaticamente. **session_id** é chave de sessão (não vem de UserContext/user_loader): use apenas o parâmetro `session_id` ou o `session_id_factory` como fonte única.

**Documentação completa:** [atendentepro/memory/README.md](atendentepro/memory/README.md)

---

## 🤝 Suporte

- 📧 **Email:** contato@monkai.com.br
- 🌐 **Site:** https://www.monkai.com.br

**Documentação adicional:** [atendentepro/service/README.md](atendentepro/service/README.md) (servidor multi-tenant), [docs/CI.md](docs/CI.md) (pipeline de CI), [docs/PUBLISHING.md](docs/PUBLISHING.md) (publicação), [docs/WORKFLOW_PYPI_EXPLAINED.md](docs/WORKFLOW_PYPI_EXPLAINED.md) (workflow PyPI), [docs/PRODUCTION_SECURITY.md](docs/PRODUCTION_SECURITY.md) (segurança em produção), [docs/SECURITY.md](docs/SECURITY.md) (mitigações de prompt injection), [docs/AUDIT_REPORT.md](docs/AUDIT_REPORT.md) (auditoria R5), [docs/AUDIT_REPORT.html](docs/AUDIT_REPORT.html) (auditoria R5 — versão HTML), [docs/QUALITY_CERTIFICATE.md](docs/QUALITY_CERTIFICATE.md) (certificado de qualidade — serial e verificação), [docs/QUALITY_CERTIFICATE.html](docs/QUALITY_CERTIFICATE.html) (certificado — versão HTML), [docs/TUNING.md](docs/TUNING.md) (módulo de tuning), [docs/fluxogramas/](docs/fluxogramas/) (diagramas de arquitetura).

---

## 📝 Changelog

### v0.7.4 (Atual)
- **Documentacao completa do modulo service**: README dedicado, diagramas de arquitetura atualizados, variaveis de ambiente documentadas
- **README principal**: Nova secao "Servidor Multi-Tenant", `pip install atendentepro[server]`, changelog atualizado

### v0.7.3
- **Servidor multi-tenant (`atendentepro.service`)**: Novo subpacote com servidor FastAPI para gerenciar redes de agentes por tenant via REST API (`/health`, `/setup`, `/chat`)
- **API generica**: `tenant_id` em vez de nomes especificos de dominio; campo `metadata` livre para contexto customizado
- **Validacao de YAMLs**: Endpoint `/setup` valida cada YAML individualmente e retorna erro 400 com nome do config invalido
- **Knowledge items como contexto**: Items do knowledge_config sao convertidos para o campo `about` do KnowledgeConfig (contexto direto, sem RAG)
- **Fix `save_embeddings_npz`**: Corrigido `dtype=object` incompativel com `allow_pickle=False` no `load_embeddings`
- **Docker**: `Dockerfile.service` para deploy no Railway ou qualquer plataforma Docker
- **Cython**: Subpacote `service/` excluido da compilacao (FastAPI + Pydantic, codigo server-side)

### v0.6.26
- **Seguranca — SQL injection corrigido**: Exemplo `multi_knowledge` reescrito com queries parametrizadas e whitelist de tabelas/colunas
- **Seguranca — Proxy confiavel**: `X-Forwarded-For` so aceito de IPs em `PROXY_TRUSTED_IPS`; padrao seguro (IP direto)
- **Seguranca — Mensagens de erro**: `str(e)` removido de `license.py` e exemplos; mensagens genericas + `logger.warning`
- **Escalabilidade — TTL no cache de guardrails**: `_GUARDRAIL_CACHE` com TTL configuravel via `ATENDENTEPRO_GUARDRAIL_CACHE_TTL` (default 300s)
- **Escalabilidade — API versioning**: Rotas do servidor de validacao sob `/v1/` com aliases legacy para compatibilidade
- **Escalabilidade — Structured logging**: `JSONFormatter` ativado com `ATENDENTEPRO_LOG_FORMAT=json`; `configure_logging()` exportado
- **Escalabilidade — docker-compose**: `server/docker-compose.yml` para desenvolvimento local do servidor
- **Escalabilidade — Docs multi-instancia**: `server/README.md` com guia Redis/DB para revocation list em clusters
- **Usabilidade — Typo corrigido**: `AtendentProConfig` renomeado para `AtendenteProConfig` (alias mantido para compatibilidade)
- **Usabilidade — Tipagem melhorada**: Reducao de `Any` em `memory/runner.py` (Protocol) e `network.py` (Union types para handoffs)
- **Usabilidade — Cobertura 65%**: Meta elevada para 65% com 33 novos testes (193 total, 65.04%)
- **Certificado de qualidade**: Auditoria R5 (revalidação independente), serial `MONKAI-AP-0626-F59FC5E769C0CE46`, nota **8.4/10** (Segurança 8.9, Usabilidade 8.4, Escalabilidade 7.9)

### v0.6.24–0.6.25
- **Rate limiter TTL/LRU**: Evicao automatica de usuarios inativos para evitar crescimento ilimitado de memoria (`max_users`, `active_users`)
- **HTTP retry com backoff**: Chamadas HTTP (license validation, webhooks) agora fazem ate 3 tentativas com backoff exponencial (0.5s, 1s, 2s)
- **Webhook HMAC-SHA256**: Webhook de escalacao agora assina payloads com `X-Webhook-Signature` via `ESCALATION_WEBHOOK_SECRET`
- **CORS configuravel**: Servidor de validacao com `CORSMiddleware` via `CORS_ALLOWED_ORIGINS`
- **pytest-cov**: Cobertura de testes monitorada no CI (meta 65%, ver `pyproject.toml`)
- **Escalation migrado para httpx**: Unificacao de client HTTP (removido `requests`)

### v0.6.23
- **Persistencia revocation list**: Tokens revogados salvos em JSON, sobrevivem restarts
- **mypy zero divida**: `agents.*`, `memory.*`, `setup_copilot` verificados sem erros
- **Build CI condicional**: Job `build` so roda apos testes passarem
- **Testes feedback persistence**: 23 novos testes

### v0.6.22
- **Rate limiting no servidor**: `/validate` (60 req/min) e `/revoke` (10 req/min) com sliding window por IP
- **Persistencia tickets por cliente**: Storage isolado em `<templates_root>/<client>/tickets.json`
- **Seguranca producao**: Modo producao (`ATENDENTEPRO_PRODUCTION=1`), exigencia de `UserContext`, verificacao de guardrails

### v0.6.21
- **Rate Limiter embutido**: `RateLimiter` (sliding window, thread-safe) exportado na API publica
- **Servidor de validacao online**: FastAPI com `/validate`, `/revoke`, `/health`
- **Testes de integracao**: 65 testes cobrindo licenciamento, RBAC, guardrails e servidor

### v0.6.20
- **Seguranca**: Chave HMAC removida do codigo, geracao de tokens removida do pacote, validacao online real, pickle eliminado, CI bloqueante, pre-filtro jailbreak, thread-safety licenca

### v0.6.15
- **Memoria de contexto longo (GRKMemory)**: `run_with_memory`, `create_grk_backend`; `pip install atendentepro[memory]`
- **Tuning (Post-Training)**: Modulo opcional para melhorar YAMLs com base em feedback e Trace

### v0.6.9
- **Correções**: Serialização do tool RAG (`go_to_rag`) para compatibilidade com MonkAI Trace; exportações de `load_feedback_config`, `load_escalation_config`, `load_answer_config` e modelos de config no pacote `templates`
- **0.6.7–0.6.8**: Configurações YAML do Feedback, Escalation e Answer passam a ser carregadas e aplicadas; persistência de tickets em JSON; tipos de ticket e prioridades configuráveis
- **0.6.6**: User Loader (carregamento automático de usuários), parâmetros `user_loader` e `auto_load_user` em `create_standard_network`

### v0.6.1
- Documentação PyPI atualizada com AgentStyle e changelog completo

### v0.6.0
- **AgentStyle**: Nova classe para personalizar tom e estilo de comunicação
  - `tone`, `language_style`, `response_length`, `custom_rules`
- `style_config.yaml`: Configuração de estilos via YAML
- Parâmetros `global_style` e `agent_styles` em `create_standard_network()`
- Todos os agentes aceitam `style_instructions`

### v0.5.9
- Descrição PyPI formal: "Framework de orquestração de agentes IA"
- README profissional com foco em capacidades corporativas

### v0.5.8
- Novos keywords: triage, handoff, escalation, feedback, knowledge-base
- Dependência `tracing` agora usa `monkai-trace`

### v0.5.7
- **MonkAI Trace**: Integração completa para monitoramento de agentes
- Novas funções: `configure_monkai_trace`, `run_with_monkai_tracking`
- Suporte multi-usuário para WhatsApp/chat

### v0.5.6
- **Agentes configuráveis**: `include_knowledge=False`, `include_flow=False`, etc.
- Permite criar redes sem agentes específicos

### v0.5.5
- Workflow PyPI apenas com tags de versão

### v0.5.4
- Documentação completa standalone no PyPI

### v0.5.3
- Links de documentação corrigidos para PyPI

### v0.5.2
- Contatos atualizados (monkai.com.br)

### v0.5.1
- Prompts modulares para Escalation e Feedback
- Remoção de handoff circular Answer→Interview

### v0.5.0
- **Novo**: Feedback Agent (tickets/SAC)
- Ferramentas: criar_ticket, consultar_ticket, listar_meus_tickets

### v0.4.0
- **Novo**: Escalation Agent (transferência humana)
- Verificação de horário, prioridade automática, webhooks

### v0.3.0
- Sistema de licenciamento com tokens
- Publicação inicial no PyPI

### v0.2.0
- Arquitetura modular completa
- 8 agentes especializados
- Sistema de templates YAML

---

**Made with ❤️ by [MonkAI](https://www.monkai.com.br)**
