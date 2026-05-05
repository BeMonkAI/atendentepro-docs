# Passo 5 (opcional): Memória de contexto longo

## Quando usar

Aplicar este passo apenas se o projeto precisar de **memória de contexto longo**: buscar conversas anteriores e injetar no contexto, e persistir cada turno para recuperação futura (módulo GRKMemory).

## Instalação

```bash
pip install atendentepro[memory]
```

## Variável de ambiente

No `.env`:

```env
GRKMEMORY_API_KEY=seu-token-grkmemory
```

## Código mínimo

1. Criar o backend e atribuir à rede.
2. Usar `run_with_memory` em vez de `Runner.run` para o agente que deve ter memória.

```python
from atendentepro.memory import run_with_memory, create_grk_backend

# Criar backend (usa GRKMEMORY_API_KEY do ambiente)
backend = create_grk_backend()
network.memory_backend = backend

# Rodar com memória: busca memórias, injeta contexto, executa agente, salva turno
result = await run_with_memory(network, network.triage, messages)
print(result.final_output)
```

## user_id e session_id (multi-usuário e canal compartilhado)

Em ambiente com mais de um usuário ou quando um mesmo canal (WhatsApp, e-mail, Teams) atende vários clientes, é essencial isolar memórias por usuário/sessão:

- **user_id**: identificar o cliente naquela conversa (ex.: número do contato, e-mail do remetente). Passar em cada chamada ou garantir que o user_loader retorne o user_id do request atual.
- **session_id**: pode ser o identificador do canal (ex.: `whatsapp_5511999999999`) ou da conversa; em canal compartilhado, session_id = canal, user_id = cliente.

Exemplo com parâmetros explícitos:

```python
result = await run_with_memory(
    network, network.triage, messages,
    user_id="5511888777666",
    session_id="whatsapp_5511999999999",
)
```

Ou definir `network.session_id_factory` para derivar o session_id (ex.: do request) e passar apenas `user_id`. Ver exemplos completos em [docs/examples/memory_user_session/](../examples/memory_user_session/).

## Nota para o Copilot

Aplicar este passo somente se o usuário pedir memória de longo prazo. Caso sim, configurar o backend e usar `run_with_memory`; em ambiente multi-usuário ou canal compartilhado, garantir que `user_id` (e `session_id` quando aplicável) sejam passados ou resolvidos em cada chamada.
