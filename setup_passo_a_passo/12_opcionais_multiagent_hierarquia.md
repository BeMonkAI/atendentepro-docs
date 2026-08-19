# Passo 12 (opcional): hierarquia multi-agente (`call_agent`)

> **Issues:** [#147 — AgentMetadata side-car](https://github.com/BeMonkAI/atendentepro/issues/147) · [#148 — invoke_agent + MultiAgentState](https://github.com/BeMonkAI/atendentepro/issues/148) · [#149 — call_agent built-in tool](https://github.com/BeMonkAI/atendentepro/issues/149)
> **Plano:** [docs/plans/2026-05-06-multi-agent.md](../plans/2026-05-06-multi-agent.md)

## Quando aplicar

Use este passo quando o produto precisar de:

- **um agente "manager"** que decide qual especialista resolve o pedido
  (ex.: roteamento por dominio: `valuation_specialist`, `risk_specialist`, ...);
- **especialistas internos** que NUNCA devem receber a mensagem do
  usuario diretamente — apenas via chamada do manager;
- **payload estruturado** (Pydantic) entre manager e especialista, em
  vez de texto livre.

Nao aplicar nas redes padrao (Triage → Flow → Answer): o pipeline
sequencial classico continua sendo o default. A hierarquia e
**aditiva** — sem `multiagent_config.yaml` o comportamento e
byte-for-byte igual ao da v0.24.

---

## API completa

```yaml
# multiagent_config.yaml
agents:
  manager:
    can_call: ["valuation_specialist", "risk_specialist"]
    builtin_tools: ["call_agent"]

  valuation_specialist:
    exposed_to_user: false
    output_schema: client_resources.signals.ValuationSignal

  risk_specialist:
    exposed_to_user: false
    output_schema: client_resources.signals.RiskSignal
```

### Campos por agente

| Campo | Tipo | Default | Status | Descricao |
|---|---|---|---|---|
| `exposed_to_user` | `bool` | `True` | ativo (v0.25) | Quando `False`, o Triage NAO pode rotear mensagens do usuario para este agente. So pode ser invocado por outro agente via `call_agent`. |
| `can_call` | `list[str]` | `[]` | ativo (v0.25) | Whitelist de agentes que este agente pode invocar. Lista vazia = sem permissao para chamar ninguem (o sentinel `call_agent` falha com `CallAgentForbidden`). |
| `output_schema` | `Optional[str]` | `None` | ativo (v0.25) | Dotted path de uma classe `pydantic.BaseModel` (ex.: `client_resources.signals.MySignal`). `invoke_agent` valida o `final_output` contra ela com 1 retry; falha de novo levanta `AgentOutputSchemaError`. |
| `builtin_tools` | `list[str]` | `[]` | ativo (v0.25) | Sentinels de tools embutidos. Hoje so `"call_agent"` e reconhecido — a `network factory` substitui pelo `function_tool` bound ao caller (whitelist `can_call` aplicada em runtime). |

> **Allowlist de `output_schema`:** por seguranca, o resolver so importa
> classes sob o prefixo `client_resources.` (mesmo padrao do
> `network_type='custom_module'`, issue #87). Para liberar prefixos
> adicionais use `ATENDENTEPRO_OUTPUT_SCHEMA_PREFIX="meu_pacote."` ou
> `ATENDENTEPRO_ALLOW_ANY_OUTPUT_SCHEMA=1` (NAO recomendado em
> producao).

---

## Exemplo 1 — Manager + 2 especialistas (recomendado)

```yaml
# client_templates/meu_cliente/multiagent_config.yaml
agents:
  manager:
    can_call: ["valuation_specialist", "risk_specialist"]
    builtin_tools: ["call_agent"]

  valuation_specialist:
    exposed_to_user: false
    output_schema: client_resources.signals.ValuationSignal

  risk_specialist:
    exposed_to_user: false
    output_schema: client_resources.signals.RiskSignal
```

```python
# client_resources/signals.py
from typing import Literal
from pydantic import BaseModel, Field

class ValuationSignal(BaseModel):
    verdict: Literal["approve", "reject", "neutral"]
    fair_price: float
    reasoning: str

class RiskSignal(BaseModel):
    verdict: Literal["approve", "reject", "escalate"]
    risk_score: int = Field(ge=0, le=100)
    reasoning: str
```

A `network factory` (`create_standard_network` ou
`create_custom_network`) le `multiagent_config.yaml`, aplica
`AgentMetadata` em `network.agent_metadata` e — para todo agente que
declarou `builtin_tools: ["call_agent"]` — anexa um `function_tool`
chamado `call_agent` cuja whitelist e o `can_call` daquele caller.

```python
from atendentepro import create_standard_network

network = create_standard_network(
    templates_root=Path("config"),
    client="meu_cliente",
)
# network.manager ja tem o tool call_agent bound ao caller "manager"
# network.valuation_specialist e network.risk_specialist tem
# exposed_to_user=False, entao Triage nao roteia mensagens diretas
# para eles.
```

## Exemplo 2 — `invoke_agent` direto (sem `call_agent`)

Quando voce precisa orquestrar de fora do LLM (ex.: codigo Python
sequencial, batch processing), use o helper diretamente:

```python
from atendentepro import (
    AgentMetadata,
    MultiAgentState,
    invoke_agent,
    create_custom_network,
)

network = create_custom_network(...)
network.agent_metadata["risk_specialist"] = AgentMetadata(
    exposed_to_user=False,
    output_schema="client_resources.signals.RiskSignal",
)

state = MultiAgentState()
signal = await invoke_agent(
    network.risk_specialist,
    payload={"deal_id": "ACME-001", "exposure": 1_000_000},
    parent_state=state,
    network=network,
)
# signal e uma instancia de RiskSignal (ou levanta AgentOutputSchemaError)
print(signal.verdict, signal.risk_score)
print(state.agent_calls)  # {"risk_specialist": <RiskSignal ...>}
```

`invoke_agent` e **one-shot**: ignora historico do caller, nao chama
`user_loader`, e renderiza `payload` como uma unica mensagem `user`
serializada via `json.dumps`. E o ponto certo para chamadas estruturadas;
para conversas multi-turn use a network normal.

## Exemplo 3 — Apenas em Python (sem YAML)

Para cenarios programaticos (testes, prototipos) voce pode atribuir
metadata e construir o tool sem tocar o YAML:

```python
from atendentepro import (
    AgentMetadata,
    build_call_agent_tool,
    create_custom_network,
)

network = create_custom_network(...)
network.agent_metadata = {
    "manager": AgentMetadata(
        can_call=["risk_specialist"],
        builtin_tools=["call_agent"],
    ),
    "risk_specialist": AgentMetadata(
        exposed_to_user=False,
        output_schema="client_resources.signals.RiskSignal",
    ),
}

# Bind manualmente (a factory faria isso automaticamente):
tool = build_call_agent_tool(network, caller_name="manager")
network.manager.tools.append(tool)
```

---

## Diagnostico — exceções típicas

| Exception | Quando dispara | Como resolver |
|---|---|---|
| `CallAgentForbidden` | LLM tentou chamar `name=X` mas `X not in caller.can_call`. | Adicione `X` ao `can_call` do caller no YAML (ou ajuste o prompt do manager para nao tentar essa rota). |
| `UnknownAgentError` | `name` esta na whitelist mas o agente nao existe na `AgentNetwork`. | Drift entre YAML e a network: o nome do `multiagent_config.yaml` precisa bater com o atributo (`network.<nome>`) ou com `agent.name`. |
| `AgentOutputSchemaError` | Sub-agente devolveu output que falhou `model_validate` em duas tentativas seguidas. | Reforce o prompt do especialista (peça JSON explícito) ou alargue o schema. O `__cause__` carrega o `ValidationError` original. |
| `OutputSchemaNotAllowedError` | `output_schema` declarado fora do allowlist (`client_resources.` por padrao). | Mova a classe para `client_resources/`, use `ATENDENTEPRO_OUTPUT_SCHEMA_PREFIX` ou (NAO recomendado em prod) `ATENDENTEPRO_ALLOW_ANY_OUTPUT_SCHEMA=1`. |

Todas as 4 exceções derivam de `Exception`/`RuntimeError` e podem ser
capturadas individualmente; o SDK serializa `CallAgentForbidden` /
`UnknownAgentError` como `tool_result` de erro para o LLM, permitindo
que o manager reaja (apologise, troque de especialista, escale).

---

## Como funciona o `call_agent` por baixo

1. `create_standard_network` lê `multiagent_config.yaml` e popula
   `network.agent_metadata`.
2. Para cada agente com `builtin_tools: ["call_agent"]`, a factory chama
   `build_call_agent_tool(network, caller_name=<agente>)` e anexa o
   resultado a `agent.tools`.
3. Em runtime, quando o LLM emite a tool call
   `call_agent(name="risk_specialist", payload={...})`:
   - a closure verifica `name in network.agent_metadata[caller_name].can_call`
     → senão, levanta `CallAgentForbidden`;
   - resolve o agente alvo via `getattr(network, name, None)` (fallback
     em `get_all_agents()`) → senão, `UnknownAgentError`;
   - mint `MultiAgentState()` fresh e chama `invoke_agent`;
   - serializa o resultado para JSON (`BaseModel.model_dump_json` ou
     `{"text": "..."}`) e devolve ao LLM.
4. Um log estruturado (`logger.info("multiagent.call_agent", extra={...})`)
   é emitido por chamada com `caller`, `callee`, `payload_keys` (apenas
   chaves) e `result_summary` (200 chars).

> **PR2 trara:** threading do `parent_state` real através das chamadas
> aninhadas (hoje o tool sempre cria um `MultiAgentState` novo) e
> instrumentação com `monkai-trace` espelhando a hierarquia de spans.
> Veja `docs/setup_passo_a_passo/13_opcionais_multiagent_ensemble.md`
> (publicado no PR2) para o pattern de ensemble (manager invoca N
> especialistas em paralelo).

---

## Cuidados

- **Nunca** marque o agente Triage como `exposed_to_user: false` — o
  Triage e o ponto de entrada do usuario. A factory nao impede isso
  hoje, mas a rede ficara sem porta de entrada.
- `output_schema` e resolvido por dotted path. Mantenha as classes em
  `client_resources/` (default) e cuide para que o pacote esteja no
  `PYTHONPATH` do runtime (Railway / Azure Functions etc).
- O LLM precisa entender que `payload` e um dict JSON-serializavel.
  Documente os campos obrigatorios no prompt do manager.
- Loop de `call_agent`: hoje o sistema NAO previne ciclos
  (`A.can_call=[B]`, `B.can_call=[A]`). Confie no orçamento de tokens
  e nas guardrails do LLM; a deteção formal de ciclos virá em PR3.

## Exemplo executável

Veja [docs/examples/multiagent/hierarchy/](../examples/multiagent/hierarchy/)
para um exemplo end-to-end completo (manager + 2 especialistas) que roda
sem credenciais (usa stub do `Runner.run`).

## Referências

- [Issue #147](https://github.com/BeMonkAI/atendentepro/issues/147) — `AgentMetadata` side-car
- [Issue #148](https://github.com/BeMonkAI/atendentepro/issues/148) — `invoke_agent` + `MultiAgentState`
- [Issue #149](https://github.com/BeMonkAI/atendentepro/issues/149) — `call_agent` built-in tool
- [`atendentepro/multiagent/`](../../atendentepro/multiagent/) — implementação (público via `from atendentepro import ...`)
