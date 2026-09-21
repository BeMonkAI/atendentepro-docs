# Multi-Knowledge Example 📚

Este diretório contém exemplos de como usar **múltiplos Knowledge Agents** e integrar **múltiplas fontes de dados**.

## 📁 Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `network.py` | Múltiplos Knowledge Agents especializados |
| `knowledge_sources_example.py` | Knowledge Agent com CSV, Banco, APIs |

---

# 1. Múltiplos Knowledge Agents

Exemplo de cliente que utiliza **múltiplos Knowledge Agents** especializados em diferentes bases de conhecimento.

## 🏗️ Arquitetura

```
                              ┌─────────────────┐
                              │     Triage      │
                              └────────┬────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
                 ▼                     ▼                     ▼
       ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
       │   Knowledge     │   │   Knowledge     │   │   Knowledge     │
       │   Técnico       │   │   FAQ           │   │   Políticas     │
       │   (Manuais)     │   │   (Tutoriais)   │   │   (Termos)      │
       └─────────────────┘   └─────────────────┘   └─────────────────┘
              │                      │                      │
              └──────────────────────┼──────────────────────┘
                                     │
                              (podem se transferir
                               entre si conforme
                               o tipo de pergunta)
```

## 📂 Knowledge Agents

### 1. Knowledge Técnico
- **Especialidade:** Documentação técnica, manuais, especificações
- **Quando usar:** Perguntas sobre instalação, configuração, APIs, troubleshooting
- **Linguagem:** Técnica e precisa

### 2. Knowledge FAQ
- **Especialidade:** Perguntas frequentes, tutoriais, guias de uso
- **Quando usar:** Dúvidas comuns, "como fazer", dicas
- **Linguagem:** Simples e acessível

### 3. Knowledge Políticas
- **Especialidade:** Termos, políticas, procedimentos
- **Quando usar:** Reembolso, cancelamento, privacidade, compliance
- **Linguagem:** Formal e precisa

## 🚀 Como Usar

### 1. Instalar dependências

```bash
pip install atendentepro
```

### 2. Preparar os embeddings

Cada Knowledge Agent precisa de seu próprio arquivo de embeddings:

```
data/
├── tecnico_embeddings.pkl    # Documentação técnica
├── faq_embeddings.pkl        # FAQs e tutoriais
└── politicas_embeddings.pkl  # Termos e políticas
```

### 3. Criar a rede

```python
from pathlib import Path
from atendentepro import activate
from client_templates.multi_knowledge_example import create_multi_knowledge_network

# Ativar
activate("ATP_seu-token")

# Criar rede com múltiplos knowledge
network = create_multi_knowledge_network(
    templates_root=Path("./templates"),
    embeddings_tecnico=Path("./data/tecnico_embeddings.pkl"),
    embeddings_faq=Path("./data/faq_embeddings.pkl"),
    embeddings_politicas=Path("./data/politicas_embeddings.pkl"),
)

# Usar
from agents import Runner

result = await Runner.run(
    network.triage,
    [{"role": "user", "content": "Como faço para cancelar?"}]
)
```

## 🔄 Fluxo de Handoffs

```
Triage ──► Knowledge Técnico, Knowledge FAQ, Knowledge Políticas, Flow

Knowledge Técnico ──► Triage, Knowledge FAQ, Knowledge Políticas
Knowledge FAQ ──► Triage, Knowledge Técnico, Knowledge Políticas
Knowledge Políticas ──► Triage, Knowledge Técnico, Knowledge FAQ

Flow ──► Interview ──► Answer ──► Triage
```

**Importante:** Os Knowledge Agents podem se transferir entre si! Se o usuário perguntar algo técnico para o FAQ Agent, ele transfere para o Técnico automaticamente.

## 📝 Exemplos de Perguntas

| Pergunta | Roteamento |
|----------|------------|
| "Como instalar a API?" | → Knowledge Técnico |
| "Como funciona o produto?" | → Knowledge FAQ |
| "Qual a política de reembolso?" | → Knowledge Políticas |
| "Quero falar com alguém" | → Escalation Agent |
| "Tenho uma sugestão" | → Feedback Agent |

## ⚙️ Configuração Avançada

### Sem RAG (apenas instruções)

```python
# Sem embeddings - os agentes funcionam apenas com as instruções
network = create_multi_knowledge_network(
    templates_root=Path("./templates"),
    # Não passa embeddings_path
)
```

### Com Escalation e Feedback

```python
network = create_multi_knowledge_network(
    templates_root=Path("./templates"),
    include_escalation=True,   # Padrão: True
    include_feedback=True,     # Padrão: True
)
```

### Apenas Knowledge Agents

```python
network = create_multi_knowledge_network(
    templates_root=Path("./templates"),
    include_escalation=False,
    include_feedback=False,
)
```

## 📊 Quando usar múltiplos Knowledge Agents?

✅ **Use quando:**
- Tem bases de conhecimento muito distintas
- Precisa de especialização diferente para cada tipo de conteúdo
- Quer linguagem/tom diferentes por área
- Precisa de métricas separadas por área

❌ **Não use quando:**
- Uma única base de conhecimento é suficiente
- O conteúdo é homogêneo
- Quer simplificar a arquitetura

## 🔧 Customização

Você pode criar quantos Knowledge Agents precisar:

```python
# Exemplo: E-commerce com múltiplos conhecimentos
knowledge_produtos = create_knowledge_agent(name="Knowledge Produtos", ...)
knowledge_envio = create_knowledge_agent(name="Knowledge Envio", ...)
knowledge_pagamentos = create_knowledge_agent(name="Knowledge Pagamentos", ...)
knowledge_trocas = create_knowledge_agent(name="Knowledge Trocas", ...)
```

---

# 2. Knowledge Agent com Múltiplas Fontes de Dados

O arquivo `knowledge_sources_example.py` demonstra como criar um Knowledge Agent que integra:

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE AGENT                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  📄 RAG     │  │  📊 CSV     │  │  🗄️ SQL    │  │  🌐 API     │ │
│  │  Documents  │  │  Tables     │  │  Database   │  │  External   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │                │        │
│         └────────────────┴────────────────┴────────────────┘        │
│                                   │                                 │
│                            ┌──────▼──────┐                          │
│                            │   RESPOSTA  │                          │
│                            │   UNIFICADA │                          │
│                            └─────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Fontes de Dados Suportadas

### 1. Documentos (RAG)
- PDFs, Word, TXT
- Usa embeddings para busca semântica
- Ideal para: manuais, políticas, documentação

### 2. Tabelas (CSV/Excel)
- Dados estruturados em planilhas
- Busca por texto em todas as colunas
- Ideal para: catálogos, preços, inventário

### 3. Banco de Dados (SQL)
- SQLite, PostgreSQL, MySQL
- Queries SQL para busca precisa
- Ideal para: clientes, pedidos, histórico

### 4. APIs Externas
- Chamadas HTTP em tempo real
- Integração com sistemas terceiros
- Ideal para: cotações, CEP, status

## 🚀 Como Usar

```python
from knowledge_sources_example import create_knowledge_agent_multi_source
from pathlib import Path

# Criar agente com múltiplas fontes
agent = create_knowledge_agent_multi_source(
    name="Knowledge E-Commerce",
    
    # 📄 Documentos (RAG)
    embeddings_path=Path("./docs_embeddings.pkl"),
    
    # 📊 Tabela CSV
    csv_path=Path("./produtos.csv"),
    
    # 🗄️ Banco de Dados
    db_path=Path("./vendas.db"),
    
    # 🌐 APIs Externas
    apis=[
        {
            "name": "viacep",
            "base_url": "https://viacep.com.br/ws",
            "description": "Consulta de CEPs"
        },
        {
            "name": "cotacao",
            "base_url": "https://api.cotacao.com.br",
            "headers": {"Authorization": "Bearer TOKEN"},
            "description": "Cotações em tempo real"
        }
    ]
)
```

## 🔧 Ferramentas Disponíveis

| Ferramenta | Fonte | Descrição |
|------------|-------|-----------|
| `go_to_rag` | Documentos | Busca semântica em documentos |
| `consultar_tabela_csv` | CSV | Busca em tabelas |
| `listar_colunas_csv` | CSV | Lista estrutura da tabela |
| `consultar_banco_dados` | SQL | Query no banco |
| `listar_tabelas_banco` | SQL | Lista tabelas disponíveis |
| `consultar_api_externa` | API | Chamada HTTP GET |
| `listar_apis_disponiveis` | API | Lista APIs configuradas |

## 📝 Exemplos de Perguntas

| Pergunta | Fonte Usada |
|----------|-------------|
| "Qual o preço do notebook?" | 📊 CSV |
| "Quais pedidos estão pendentes?" | 🗄️ SQL |
| "Como configurar o produto?" | 📄 RAG |
| "Qual o CEP de São Paulo?" | 🌐 API |
| "Histórico do cliente João" | 🗄️ SQL + 📊 CSV |

## ▶️ Executar Exemplo

```bash
cd docs/examples/multi_knowledge
python knowledge_sources_example.py
```

O exemplo cria automaticamente dados de teste (CSV e SQLite) e demonstra consultas em cada fonte.

---

## 📧 Suporte

- **Email:** contato@monkai.com.br
- **Site:** https://www.monkai.com.br

