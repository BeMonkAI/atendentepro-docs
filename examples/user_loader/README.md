# 👤 Exemplo: Carregamento Automático de Usuários

Este exemplo demonstra como usar o **User Loader** para identificar automaticamente usuários cadastrados e enriquecer o contexto das conversas com informações do usuário.

## O que é User Loader?

O User Loader carrega **dados do usuário** tipicamente armazenados em banco de dados (ou CSV/API que represente esse cadastro): identidade, perfil, role e dados estatísticos. **Não** use para memória de conversa nem para session_id — esses conceitos são tratados em outro lugar (módulo de memória, session_id_factory). O carregamento pode ser restrito a **um agente específico** (ex.: apenas flow): use `run_with_user_context(network, network.flow, messages)` só para esse agente; os demais podem ser chamados com `Runner.run(agent, messages)` sem carregar usuário.

O User Loader é um sistema que:

1. **Extrai identificadores** das mensagens do usuário (telefone, email, CPF, etc.)
2. **Carrega dados** do usuário de diferentes fontes (CSV, banco de dados, API)
3. **Cria UserContext** automaticamente para enriquecer o contexto
4. **Evita onboarding desnecessário** para usuários já cadastrados

## load_user e metadata

A função que você passa como `loader_func` (ex.: load_user) **busca os dados** (banco, CSV, API) e **retorna um dicionário**. O `create_user_loader` usa esse dicionário para montar o `UserContext`: as chaves `user_id` e `role` vão para os campos fixos do UserContext; **o resto do dicionário vai para `UserContext.metadata`**. Ou seja: **metadata é onde o resultado do load_user fica armazenado** no contexto.

Exemplo: se load_user retorna `{"user_id": "1", "nome": "João", "plano": "premium"}`, após `run_with_user_context` você acessa:

- `network.loaded_user_context.user_id` → `"1"`
- `network.loaded_user_context.metadata["nome"]` → `"João"`
- `network.loaded_user_context.metadata["plano"]` → `"premium"`

Os exemplos `example_csv.py` e `example_database.py` já usam `network.loaded_user_context.metadata.get("nome")`, `metadata.get("plano")` para exibir os dados carregados.

## Casos de Uso

| Cenário | Solução |
|---------|---------|
| **Usuário existente** | Identifica automaticamente e pula onboarding |
| **Personalização** | Carrega dados do usuário para respostas personalizadas |
| **Contexto enriquecido** | Todos os agentes têm acesso a informações do usuário |
| **Múltiplas fontes** | Suporta CSV, banco de dados, APIs REST, etc. |

## Arquivos

- `example_csv.py` - Exemplo usando CSV como fonte de dados
- `example_database.py` - Exemplo usando banco de dados simulado
- `users.csv` - Arquivo CSV de exemplo com usuários
- `run_example.py` - Script para executar os exemplos

## Executando

```bash
# Configurar variáveis de ambiente
export OPENAI_API_KEY=sk-...
export ATENDENTEPRO_LICENSE_KEY=ATP_...

# Executar
python run_example.py
```

## Fluxo de Carregamento

```
┌─────────────────────────────────────────────────────────────┐
│              Mensagem do Usuário                             │
│        "Olá, meu email é joao@example.com"                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              EXTRATOR DE IDENTIFICADOR                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Telefone   │  │    Email     │  │   User ID    │      │
│  │  (11) 9999...│  │ joao@ex...  │  │  12345678900 │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              LOADER DE DADOS                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     CSV      │  │   Database   │  │     API      │      │
│  │  users.csv   │  │  PostgreSQL  │  │  REST API    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              UserContext Criado                              │
│  user_id: "joao@example.com"                                │
│  role: "cliente"                                             │
│  metadata: {                                                 │
│    "nome": "João Silva",                                     │
│    "telefone": "11999998888",                                │
│    "plano": "premium"                                        │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Agentes Usam Contexto                          │
│  - Triage: Decide se vai para onboarding ou não             │
│  - Knowledge: Personaliza respostas com dados do usuário     │
│  - Answer: Usa nome e preferências do usuário                 │
└─────────────────────────────────────────────────────────────┘
```

## Funções Disponíveis

### Extratores de Identificador

```python
from atendentepro import (
    extract_phone_from_messages,
    extract_email_from_messages,
    extract_user_id_from_messages,
)

# Extrair telefone
phone = extract_phone_from_messages(messages)

# Extrair email
email = extract_email_from_messages(messages)

# Extrair user_id/CPF
user_id = extract_user_id_from_messages(messages)
```

### Criar Loader

```python
from atendentepro import create_user_loader

def load_from_db(identifier: str):
    # Sua lógica de busca
    return {"user_id": identifier, "role": "cliente", "nome": "João"}

loader = create_user_loader(
    loader_func=load_from_db,
    identifier_extractor=extract_email_from_messages
)
```

### Usar com Network

```python
from atendentepro import create_standard_network, run_with_user_context

network = create_standard_network(
    templates_root=Path("templates"),
    user_loader=loader,
    include_onboarding=True,
)

# Executar com carregamento automático
result = await run_with_user_context(
    network,
    network.triage,
    messages
)
```

## Exemplos

### 1. CSV como Fonte de Dados

```python
from pathlib import Path
from atendentepro import create_user_loader, load_user_from_csv, extract_email_from_messages

def load_user(identifier: str):
    return load_user_from_csv(
        csv_path=Path("users.csv"),
        identifier_field="email",
        identifier_value=identifier
    )

loader = create_user_loader(
    loader_func=load_user,
    identifier_extractor=extract_email_from_messages
)
```

### 2. Banco de Dados

```python
import sqlite3

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
```

### 3. API REST

```python
import httpx

async def load_from_api(identifier: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.example.com/users/{identifier}"
        )
        if response.status_code == 200:
            return response.json()
    return None

loader = create_user_loader(load_from_api, extract_email_from_messages)
```

## Integração com Onboarding

Quando um `user_loader` está configurado:

- **Usuário encontrado**: Vai direto para o triage, sem passar pelo onboarding
- **Usuário não encontrado**: É direcionado para o onboarding normalmente
- **Contexto disponível**: Todos os agentes têm acesso a `network.loaded_user_context`

## Benefícios

1. ✅ **Experiência personalizada** - Respostas baseadas em dados do usuário
2. ✅ **Menos fricção** - Usuários conhecidos não precisam fazer onboarding
3. ✅ **Contexto rico** - Todos os agentes têm acesso a informações do usuário
4. ✅ **Flexível** - Suporta múltiplas fontes de dados
5. ✅ **Automático** - Funciona transparentemente durante a conversa
