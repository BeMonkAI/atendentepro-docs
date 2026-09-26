# Exemplos: user_id e session_id com memória

Exemplos completos de uso de **user_id** e **session_id** com o módulo de memória (`run_with_memory`), para isolamento multi-tenant e por sessão/conversa.

## Requisitos

- `ATENDENTEPRO_LICENSE_KEY` e `OPENAI_API_KEY` (variáveis de ambiente ou `.env`)
- **Não** é necessário `GRKMEMORY_API_KEY`: os exemplos usam um backend de memória em memória (`MockMemoryBackend`)

## Como rodar

Na raiz do projeto ou de `docs/examples/memory_user_session`:

```bash
# Menu interativo
python docs/examples/memory_user_session/run_example.py

# Ou direto:
python docs/examples/memory_user_session/run_example.py 1   # explícito
python docs/examples/memory_user_session/run_example.py 2   # user_loader
python docs/examples/memory_user_session/run_example.py 3   # session_id_factory
python docs/examples/memory_user_session/run_example.py all # todos
```

Ou executar cada exemplo:

```bash
python docs/examples/memory_user_session/example_explicit_user_session.py
python docs/examples/memory_user_session/example_user_loader_session.py
python docs/examples/memory_user_session/example_session_id_factory.py
```

## Exemplos

### 1. user_id e session_id explícitos (`example_explicit_user_session.py`)

Passa `user_id` e `session_id` em cada chamada a `run_with_memory`:

```python
result = await run_with_memory(
    network, network.triage, messages,
    user_id="user_123",
    session_id="sess_whatsapp_abc",
)
```

- Um usuário com **duas sessões** (ex.: WhatsApp vs web): memórias separadas por `session_id`.
- **Dois usuários**: memórias isoladas por `user_id`.

### 2. user_loader só com dados do cliente; session_id por factory ou parâmetro (`example_user_loader_session.py`)

O `user_loader` é para **dados do usuário em banco** (perfil, estatísticas, role); **não** para memória ou sessão. Retorna apenas `UserContext(user_id=..., role=..., metadata=...)`. O `session_id` vem de `network.session_id_factory` (ex.: ID da conversa no request) ou do parâmetro de `run_with_memory`. Recomendado para separar responsabilidades.

```python
def loader(messages):
    return UserContext(user_id="usr_julia", role="cliente", metadata={"plano": "premium"})

network = create_standard_network(..., user_loader=loader)
network.session_id_factory = lambda n, msgs: get_conversation_id_from_request()
result = await run_with_memory(network, network.triage, messages)
```

### 3. session_id_factory na rede (`example_session_id_factory.py`)

Quando o `session_id` não é passado como parâmetro, `run_with_memory` usa `network.session_id_factory(network, messages)`:

```python
def session_by_conversation_hash(network, messages):
    user_id = None
    if getattr(network, "loaded_user_context", None):
        user_id = getattr(network.loaded_user_context, "user_id", None)
    last_n = 6
    recent = messages[-last_n:] if len(messages) >= last_n else messages
    h = hashlib.sha256((str(user_id or "") + str(recent)).encode()).hexdigest()[:16]
    return f"sess_{h}"

network.session_id_factory = session_by_conversation_hash
result = await run_with_memory(network, network.triage, messages, user_id="user_web")
```

Ou simulando um ID de canal (ex.: request):

```python
network.session_id_factory = lambda n, msgs: "whatsapp_5511999999999"
```

## Ordem de resolução de session_id

**Recomendado:** obter session_id pelo **parâmetro** ou por **`network.session_id_factory`** (request/canal). O user_loader é para dados do usuário em banco (perfil, estatísticas); não para memória ou sessão.

1. Parâmetro `session_id` em `run_with_memory` (recomendado)
2. (Legado) `loaded_user_context.session_id`
3. (Legado) `loaded_user_context.metadata["session_id"]`
4. `network.session_id_factory(network, messages)` (recomendado)
5. Parâmetro `session_id_factory(network, messages)` em `run_with_memory`

## Evitar confusão entre usuários

A memória é isolada pela chave **(user_id, session_id)** no backend: cada par identifica um “recipiente” de memórias. Se dois usuários ou duas conversas usarem a mesma chave, verão as mesmas memórias.

### Canal compartilhado (caso comum)

É normal usar um mesmo canal para vários clientes: um número de WhatsApp, uma caixa de e-mail ou um canal do Microsoft Teams atendendo múltiplos usuários. Nesse cenário:

- **session_id** pode ser o identificador do canal (ex.: `"whatsapp_5511999999999"`, `"email_suporte@empresa.com"`) — igual para todos que usam aquele canal.
- **user_id** deve ser o **identificador do cliente naquela conversa** (ex.: número do WhatsApp do contato, e-mail do remetente, ID do usuário no Teams). Assim a chave `(user_id, session_id)` continua isolando: mesmo canal, clientes diferentes.

### Situações de risco

- Não passar `user_id` em ambiente multi-usuário (e não ter user_loader que preencha por request) — em canal compartilhado isso faz todos os clientes do canal verem a mesma memória.
- Usar `session_id_factory` que retorna o mesmo valor para todos (ex.: constante) sem passar `user_id`.
- Derivar `session_id` só do conteúdo das mensagens (sem incluir `user_id` no hash).

### Recomendações

1. Identificar o usuário/cliente em cada chamada: passar `user_id` por parâmetro ou garantir que o user_loader retorne o user_id **do request atual** (ex.: extraído do JWT ou do canal).
2. Em canal compartilhado: **user_id** = cliente/contato, **session_id** = canal.
3. Se `session_id` for derivado por hash (ex.: últimas mensagens), incluir `user_id` no hash para evitar colisão entre usuários.

### Exemplo: evitar vs fazer

```python
# Evitar: sem user_id e session_id constante → todos compartilham a mesma memória
network.session_id_factory = lambda n, msgs: "default"
result = await run_with_memory(network, network.triage, messages)  # user_id=None

# Fazer: user_id identifica o cliente; session_id pode ser o canal (compartilhado) ou por parâmetro
network.session_id_factory = lambda n, msgs: "whatsapp_5511999999999"
result = await run_with_memory(network, network.triage, messages, user_id="5511888777666")
```

## Usar com GRKMemory em produção

Substitua o `MockMemoryBackend` por:

```python
from atendentepro.memory import create_grk_backend
network.memory_backend = create_grk_backend()
```

Configure `GRKMEMORY_API_KEY` e, se quiser, um backend customizado (ver [atendentepro/memory/README.md](../../../atendentepro/memory/README.md)).
