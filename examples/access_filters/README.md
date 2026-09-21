# 🔐 Exemplo: Filtros de Acesso por Role e User

Este exemplo demonstra como configurar filtros de acesso baseados em **role** (função) e **user** (usuário específico) no AtendentePro.

## O que são Filtros de Acesso?

Os filtros de acesso permitem controlar:

1. **Agentes**: Habilitar/desabilitar agentes inteiros por role/user
2. **Prompts**: Adicionar seções condicionais aos prompts por role/user
3. **Tools**: Habilitar/desabilitar tools específicas por role/user

## Casos de Uso

| Cenário | Solução |
|---------|---------|
| **Multi-tenant** | Diferentes clientes veem diferentes agentes |
| **Níveis de acesso** | Admin vê mais opções que cliente |
| **Segurança** | Dados sensíveis só para roles específicas |
| **Personalização** | Diferentes instruções por departamento |

## Arquivos

- `access_config.yaml` - Configuração via YAML
- `example_via_code.py` - Configuração via código Python
- `example_via_yaml.py` - Carregamento de configuração YAML
- `example_multiuser.py` - Exemplo com múltiplos usuários
- `run_example.py` - Script para executar os exemplos

## Executando

```bash
# Configurar variáveis de ambiente
export OPENAI_API_KEY=sk-...
export ATENDENTEPRO_LICENSE_KEY=ATP_...

# Executar
python run_example.py
```

## Fluxo de Verificação

```
┌─────────────────────────────────────────────────────────────┐
│                    Requisição do Usuário                     │
│                  user_id="123", role="vendedor"              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FILTRO DE AGENTES                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Knowledge  │  │  Escalation │  │   Feedback  │          │
│  │  ✅ Allowed  │  │  ✅ Allowed  │  │  ❌ Denied   │          │
│  │ (vendedor)  │  │ (not denied)│  │ (only admin)│          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FILTRO DE PROMPTS                         │
│  Knowledge Agent recebe prompt BASE +                        │
│  ┌──────────────────────────────────────────────────┐       │
│  │ "## Capacidades de Vendedor                      │       │
│  │  Você pode oferecer: desconto máximo 15%..."     │       │
│  └──────────────────────────────────────────────────┘       │
│  (seção condicional para role="vendedor")                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FILTRO DE TOOLS                           │
│  Tools disponíveis para vendedor:                            │
│  ✅ consultar_estoque                                        │
│  ✅ consultar_comissao                                        │
│  ❌ aprovar_desconto_especial (só gerente)                   │
│  ❌ deletar_cliente (só admin)                               │
└─────────────────────────────────────────────────────────────┘
```

## Tipos de Filtro

### 1. Whitelist (allowed_*)

Somente os listados podem acessar:

```python
# Somente admin e gerente
AccessFilter(allowed_roles=["admin", "gerente"])

# Somente usuários específicos
AccessFilter(allowed_users=["user_vip_1", "user_vip_2"])
```

### 2. Blacklist (denied_*)

Todos exceto os listados podem acessar:

```python
# Todos exceto clientes
AccessFilter(denied_roles=["cliente"])

# Todos exceto usuários específicos
AccessFilter(denied_users=["user_bloqueado"])
```

### 3. Combinado

Regras podem ser combinadas:

```python
# Admin/gerente, exceto usuários específicos
AccessFilter(
    allowed_roles=["admin", "gerente"],
    denied_users=["admin_suspenso"]
)
```

## Prioridade de Avaliação

1. `denied_users` - Se usuário está negado, bloqueia
2. `allowed_users` - Se lista existe e usuário está nela, permite
3. `denied_roles` - Se role está negada, bloqueia
4. `allowed_roles` - Se lista existe e role não está nela, bloqueia
5. **Permite por padrão** - Se nenhum filtro matched
