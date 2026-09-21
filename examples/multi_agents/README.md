# 🔀 Exemplo: Múltiplos Agentes (2 Interview + 2 Knowledge)

Este exemplo demonstra como criar uma rede de agentes com **múltiplas instâncias** de Interview e Knowledge agents, cada um especializado em um domínio diferente.

## Caso de Uso

Uma empresa que atende dois tipos de clientes:
- **Pessoa Física (PF)**: Produtos de consumo
- **Pessoa Jurídica (PJ)**: Soluções empresariais

Cada tipo precisa de:
- Entrevista diferente (coleta de dados específicos)
- Base de conhecimento diferente (produtos/serviços distintos)

## Arquitetura

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
    │  (consumo)  │  │ (empresas)  │
    └─────────────┘  └─────────────┘
```

## Arquivos

- `example_multi_agents.py` - 2 Interview + 2 Knowledge (PF/PJ)
- `example_one_interview_two_knowledge.py` - 1 Interview → 2 Knowledge (Suporte)
- `run_example.py` - Script para executar

## Como Funciona

### 1. Criar agentes especializados

```python
# Interview para Pessoa Física
interview_pf = create_interview_agent(
    interview_questions="CPF, data de nascimento, renda mensal",
    name="interview_pf",
)

# Interview para Pessoa Jurídica
interview_pj = create_interview_agent(
    interview_questions="CNPJ, razão social, faturamento anual",
    name="interview_pj",
)
```

### 2. Configurar handoffs personalizados

```python
# Triage direciona para o interview correto
triage.handoffs = [interview_pf, interview_pj, knowledge_pf, knowledge_pj]

# Cada interview direciona para seu knowledge
interview_pf.handoffs = [knowledge_pf, triage]
interview_pj.handoffs = [knowledge_pj, triage]
```

### 3. Usar `create_custom_network`

```python
network = create_custom_network(
    triage=triage,
    custom_agents={
        "interview_pf": interview_pf,
        "interview_pj": interview_pj,
        "knowledge_pf": knowledge_pf,
        "knowledge_pj": knowledge_pj,
    }
)
```

## Executando

```bash
export OPENAI_API_KEY=sk-...
export ATENDENTEPRO_LICENSE_KEY=ATP_...

python run_example.py
```

## Dicas

1. **Nomes únicos**: Cada agente precisa de um `name` único
2. **Handoffs claros**: Configure quais agentes cada um pode chamar
3. **Triage inteligente**: Inclua keywords claras para direcionar PF vs PJ
4. **Contexto compartilhado**: Use `ContextNote` para passar dados entre agentes
