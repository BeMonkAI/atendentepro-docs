# 19 — Long-term memory: `memory_context_block_tag`

Issue [#271](https://github.com/BeMonkAI/atendentepro/issues/271) — para clientes que injetam memoria cross-session como bloco XML (`<long_term_memory>...</long_term_memory>` ou similar) em uma mensagem de sistema, esta opcao instrui automaticamente todos os agentes da rede a ler e usar o bloco — sem precisar duplicar a instrucao em `custom_prompt_prefix`/`custom_prompt_suffix` de cada agente.

## 19.1 — Problema

Em deployments com memoria de longo prazo (ex: GRKMemory), o pipeline tipico e:

1. **Recall**: a cada turno, recuperar fatos relevantes da memoria (RAG sobre sessoes passadas).
2. **Inject**: embrulhar em `<long_term_memory>...</long_term_memory>` e prepend como mensagem `system` no payload de `Runner.run`.
3. **Consume**: cada agente da rede precisa saber que o bloco existe e como usa-lo.

Pre-#271, o passo 3 era responsabilidade do cliente: cada agente precisava de uma instrucao explicita no prompt para ler o bloco. Em uma rede de 5+ agentes (Triage, Flow, Answer, Knowledge, Interview), o cliente repetia a mesma instrucao 5x. Esquecer 1 agente quebra o pipeline silenciosamente — Triage le, Flow ignora.

Caso real (Marketing Insights Nestle): instrucao presente em Triage Rule 0, ausente em Flow/Answer — comportamento inconsistente em prod ate o gap ser detectado.

## 19.2 — Uso

```python
from atendentepro import create_standard_network

network = create_standard_network(
    templates_root=Path("./client_templates"),
    client="my_client",
    memory_context_block_tag="long_term_memory",  # nome da tag XML
)
```

A lib **appenda** automaticamente o bloco abaixo no prompt de TODOS os agentes da rede:

```
## MEMÓRIA DE SESSÕES ANTERIORES
Se houver um bloco `<long_term_memory>...</long_term_memory>` no contexto da conversa (como mensagem de sistema), use o conteudo dele para enriquecer sua resposta com fatos persistentes que o usuario compartilhou em sessoes passadas.

Regras:
- NÃO mencione literalmente o bloco nem suas tags na resposta — use o conteudo apenas como contexto silencioso.
- A regra anti-alucinação numérica continua valendo: só cite numeros que vieram de `tool_outputs` da sessao atual, NUNCA de memoria.
- Quando o bloco estiver ausente, opere normalmente sem comentar a ausencia.
```

A tag (`long_term_memory` no exemplo) e interpolada — pode usar qualquer nome (`cross_session_facts`, `user_history`, etc.) desde que o cliente emita o bloco com o mesmo nome.

### Via servico multi-tenant (`TenantManager.setup` / HTTP `/setup`)

Issue [#288](https://github.com/BeMonkAI/atendentepro/issues/288) — clientes que provisionam tenants via o servico multi-tenant podem passar o campo no payload do `/setup` HTTP:

```json
POST /setup
{
  "tenant_id": "acme",
  "yamls": { "...": "..." },
  "memory_context_block_tag": "long_term_memory"
}
```

Equivalente via Python:

```python
await mgr.setup(
    tenant_id="acme",
    yamls={...},
    memory_context_block_tag="long_term_memory",
)
```

Funciona tambem com `network_config` (custom handoff graph). Empty string e tratado como `None` pelo factory (feature desativada).

## 19.3 — Combinacao com `pre_run_hook`

Padrao recomendado para integracao com backend de memoria:

```python
async def inject_memory_block(messages):
    user_id = extract_user_id(messages)  # logica do cliente
    facts = await memory_backend.recall(user_id, limit=3)
    if not facts:
        return messages
    block = "<long_term_memory>\n" + "\n".join(facts) + "\n</long_term_memory>"
    return [{"role": "system", "content": block}] + messages


network = create_custom_network(
    templates_root=Path("./client_templates"),
    client="my_client",
    network_config={...},
    memory_context_block_tag="long_term_memory",
    pre_run_hook=inject_memory_block,
)
```

- `pre_run_hook` faz a injecao da mensagem por request (issue #195).
- `memory_context_block_tag` instrui TODOS os agentes a consumir o bloco (issue #271).

Os dois trabalham juntos: o hook decide *quando* e *o que* injetar; o tag instrui *como* consumir.

## 19.4 — Defaults e backward-compat

- `memory_context_block_tag=None` (default) → byte-for-byte identico a pre-#271. Nenhum agente recebe instrucao nova.
- `memory_context_block_tag=""` (string vazia) → tratado como `None`, feature desativada.
- O bloco e **APPENDED** ao final do prompt de cada agente, apos a secao `## Estilo de Comunicação` se existir. A identidade primaria do agente e a regra de roteamento ficam no topo onde o LLM da mais peso.

## 19.5 — Anti-pattern: re-implementar via `custom_prompt_suffix`

```python
# Errado — instrucao duplicada em N agentes, drift facil.
network.triage.instructions += "\n## MEMORIA..."
network.flow.instructions += "\n## MEMORIA..."
network.answer.instructions += "\n## MEMORIA..."
# ... e quando esquecer um, o pipeline fica inconsistente sem warning.

# Certo — uma flag, todos os agentes.
network = create_standard_network(..., memory_context_block_tag="long_term_memory")
```

## 19.6 — Versionamento

Disponivel a partir da v0.39.0.
