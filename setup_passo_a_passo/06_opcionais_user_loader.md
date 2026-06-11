# Passo 6 (opcional): User loader

## Quando usar

Aplicar este passo apenas se o projeto precisar **identificar o usuário a partir da mensagem** (e-mail, telefone, etc.) e **carregar dados do usuário** de banco, CSV ou API (perfil, role, estatísticas).

## O que é o user_loader

O user_loader é uma função que recebe as mensagens e retorna um `UserContext(user_id=..., role=..., metadata=...)`. A biblioteca chama essa função antes de executar o agente (quando se usa `run_with_user_context` ou `run_with_memory`) e preenche `network.loaded_user_context`.

**Importante:** use o user_loader apenas para **dados do usuário** (cadastro, perfil, role, metadata). **Não** use para memória de conversa nem para session_id — session_id deve vir de parâmetro ou de `network.session_id_factory`.

## Snippet mínimo

```python
from atendentepro.models import UserContext

def loader(messages):
    # Em produção: extrair identificador do request (JWT, canal, etc.)
    # e buscar dados no banco/API; retornar UserContext.
    return UserContext(
        user_id="usr_123",
        role="cliente",
        metadata={"plano": "premium"},
    )

network = create_standard_network(
    templates_root=Path("config"),
    client="meu_cliente",
    user_loader=loader,
)
```

O user_loader deve retornar dados do **request atual** (não reutilizar contexto de outro usuário). Ver [07_cuidados_principais.md](07_cuidados_principais.md).

## session_id

Obter session_id pelo parâmetro de `run_with_memory` ou por `network.session_id_factory` (ex.: ID da conversa ou do canal no request). Não definir session_id no user_loader; manter responsabilidades separadas.

Exemplo de factory na rede:

```python
network.session_id_factory = lambda n, msgs: get_conversation_id_from_request()
```

## Campos custom do cliente (`empresa`, `aad_object_id`, etc.)

Para campos específicos do diretório corporativo do cliente, veja o padrão de subclasse em [client_context_patterns.md](../client_context_patterns.md). Use só quando precisar de typing forte para tools próprios — caso contrário, `UserContext.metadata` cobre o caso.

## Referências

- [docs/examples/user_loader/](../examples/user_loader/) — Exemplos com CSV e banco
- [docs/examples/memory_user_session/](../examples/memory_user_session/) — user_id, session_id e memória
- [docs/client_context_patterns.md](../client_context_patterns.md) — Subclasse de `UserContext` para campos custom

## Nota para o Copilot

Aplicar este passo somente se o usuário precisar de carregamento de dados do usuário por request. Manter session_id fora do user_loader; obter session_id por parâmetro ou por `network.session_id_factory`.
