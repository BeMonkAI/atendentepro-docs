# Passo 13 (opcional): ensemble multi-agente (`ParallelNetwork`)

> **Issues:** [#150 — ParallelNetwork ensemble runner](https://github.com/BeMonkAI/atendentepro/issues/150) · [#151 — YAML wiring + service-layer dispatch](https://github.com/BeMonkAI/atendentepro/issues/151)
> **Plano:** [docs/plans/2026-05-06-multi-agent.md](../plans/2026-05-06-multi-agent.md)

## Quando aplicar

Existem hoje tres formas de orquestrar agentes na lib. Escolher pelo
**formato da decisao**, nao pelo numero de agentes:

| Formato | Quando usar | Entry point |
|---|---|---|
| **Sequencial** (default) | Atendimento turn-by-turn (Triage → Flow → Answer). 1 agente fala por vez; os demais sao alvos de handoff. | `create_standard_network` / `create_custom_network` ([passo 3](03_ativacao_e_primeira_rede.md)). |
| **Hierarquia** | Cadeia em arvore: um manager LLM decide qual especialista chama em runtime via `call_agent`. | `create_standard_network` + `multiagent_config.yaml` com `builtin_tools: [call_agent]` ([passo 12](12_opcionais_multiagent_hierarquia.md)). |
| **Ensemble** | N personas opinam **EM PARALELO** sobre o mesmo input; um coordenador sintetiza os signals tipados num veredito final. | `create_parallel_network` + `multiagent_config.yaml` com `network_type: parallel` (este passo). |

O ensemble e a forma certa quando voce quer **diversidade de
perspectivas** (ex.: 3 estilos de investidor opinando sobre o mesmo
ticker, 3 especialistas medicos analisando o mesmo prontuario) e nao
quando voce quer **profundidade dirigida** (que e o caso da hierarquia).

A trilha continua sendo aditiva: sem `multiagent_config.yaml` o
comportamento e byte-for-byte igual ao da v0.24.

---

## YAML completo

```yaml
# client_templates/<seu_cliente>/multiagent_config.yaml
network_type: parallel
fanout:
  - persona_value
  - persona_growth
  - persona_macro
coordinator: portfolio_manager
parallel_timeout_s: 30.0          # default; segundos por agente do fanout
parallel_max_concurrency: 10      # default; cap simultaneo do asyncio.gather
parallel_partial_ok: false        # default; true = ignora falhas parciais

agents:
  persona_value:
    exposed_to_user: false
    output_schema: client_resources.signals.PersonaSignal
  persona_growth:
    exposed_to_user: false
    output_schema: client_resources.signals.PersonaSignal
  persona_macro:
    exposed_to_user: false
    output_schema: client_resources.signals.PersonaSignal
  portfolio_manager:
    exposed_to_user: true
    # coordinator NAO precisa declarar output_schema — sua saida e
    # texto livre voltado ao usuario final.
```

### Campos top-level

| Campo | Tipo | Default | Descricao |
|---|---|---|---|
| `network_type` | `"sequential" \| "parallel"` | `"sequential"` | `"parallel"` ativa a fabrica `create_parallel_network`. |
| `fanout` | `list[str]` | `[]` | Nomes dos agentes que rodam em paralelo. Ordem preservada na payload do coordenador. |
| `coordinator` | `str` | `""` | Nome do agente que recebe os signals e produz a string final. |
| `parallel_timeout_s` | `float` | `30.0` | Timeout **por agente** (`asyncio.wait_for`). Um lento nao para o batch. |
| `parallel_max_concurrency` | `int` | `10` | Cap de agentes simultaneos via `asyncio.Semaphore`. |
| `parallel_partial_ok` | `bool` | `False` | `False` = qualquer falha aborta com `ParallelFanoutError`. `True` = falhas individuais sao logadas e descartadas; coordenador recebe so os sobreviventes. Aborta apenas se TODOS falharem. |

### Personas precisam de `output_schema`

Cada agente do `fanout` **DEVE** declarar `output_schema` apontando para
uma subclasse de `AgentSignal` (criada via `signal_subclass` ou a mao). A
fabrica falha em build com `ParallelNetworkConfigError` se algum estiver
sem schema — o coordenador depende de signals tipados para sintetizar
algo coerente.

```python
# client_resources/signals.py
from atendentepro import signal_subclass

PersonaSignal = signal_subclass(
    "PersonaSignal",
    {
        "recommendation": (str, ""),
        "horizon_months": (int, 12),
    },
)
# PersonaSignal herda agent_name, verdict, confidence, reasoning, metadata
# de AgentSignal e adiciona recommendation + horizon_months.
```

`signal_subclass(name, extra_fields)` aceita tanto `(tipo, default)`
quanto o tipo nu (interpretado como obrigatorio sem default). O dotted
path declarado no YAML segue o mesmo allowlist do
`output_schema` da hierarquia: por padrao apenas `client_resources.` e
permitido. Para liberar outro prefixo use
`ATENDENTEPRO_OUTPUT_SCHEMA_PREFIX="meu_pacote."` ou
`ATENDENTEPRO_ALLOW_ANY_OUTPUT_SCHEMA=1` (NAO recomendado em prod).

---

## Como rodar

```python
from pathlib import Path
from atendentepro import activate, configure, create_parallel_network

activate("...")
configure(provider="openai", openai_api_key="...")

network = create_parallel_network(
    templates_root=Path("client_templates"),
    client="meu_cliente",
)
final_text = await network.run(
    [{"role": "user", "content": "Stock pick para 12 meses"}]
)
```

`network.run(messages)` faz:

1. `asyncio.gather` sobre as N personas com `Semaphore(max_concurrency)`
   e `wait_for(timeout_s)` por agente.
2. Coleta `successes` (instancias do `output_schema`) e `failures`
   (excecoes por nome).
3. Aplica a politica de `parallel_partial_ok` (ver tabela acima).
4. Chama o coordenador via `invoke_agent` passando
   `{"signals": <successes serializados>, "messages": <originais>}`.
5. Devolve a string final do coordenador (ou `model_dump_json()` se ele
   declarou um `output_schema`).

---

## Diagnostico — exceções típicas

| Exception | Quando dispara | Como resolver |
|---|---|---|
| `ParallelNetworkConfigError` | Build-time: agente do fanout/coordinator nao existe no bloco `agents`, ou agente do fanout nao declarou `output_schema`. Atributos `missing_agents` / `missing_schema`. | Conferir nomes (typo entre `fanout` e `agents:`) e adicionar `output_schema` em cada persona. |
| `ParallelFanoutError` | Runtime fanout: `partial_ok=False` e algum agente falhou; OU `partial_ok=True` e TODOS falharam. Atributos `failures` (nome → excecao) e `successes` (parciais). | Investigar a excecao em `failures[nome].__cause__` (timeout? schema mismatch?). Se a falha e tolerada, ligar `parallel_partial_ok: true`. |
| `CoordinatorError` | Runtime coordinator: agente coordenador levantou. Atributos `signals` (signals do fanout) e `cause` (excecao original; `__cause__` tambem). | Reforce o prompt do coordinator (peca formato esperado), inspecione `signals` para ver se algum esta malformado. NUNCA ha fallback silencioso para concatenar signals — corrigir o coordinator e a unica saida correta. |
| `OutputSchemaNotAllowedError` | Build-time: `output_schema` declarado fora do allowlist (`client_resources.` por padrao). | Mover a classe para `client_resources/`, usar `ATENDENTEPRO_OUTPUT_SCHEMA_PREFIX` ou (NAO recomendado em prod) `ATENDENTEPRO_ALLOW_ANY_OUTPUT_SCHEMA=1`. |

---

## Tunaveis

- **`parallel_timeout_s`** (default `30.0`) — limite **por agente**, nao
  por batch. Subir para personas com prompts longos (analise de
  documentos); descer para chamadas leves onde latencia importa mais que
  completude.
- **`parallel_max_concurrency`** (default `10`) — cobre confortavelmente
  ensembles tipicos de 3-7 personas. Reduzir quando o provider tiver
  rate-limit baixo (ex.: `5` para Azure OpenAI standard); subir so se
  precisar de fanouts grandes (>10 agentes).
- **`parallel_partial_ok`** (default `False`) — manter `False` em
  cenarios criticos (uma persona ausente muda a recomendacao). Ligar
  `True` para dashboards/sumarios onde melhor ter algo do que abortar.

---

## Multi-turn

`ParallelNetwork.run` mint um `MultiAgentState` proprio por chamada — nao
mantem historico entre invocacoes. Para conversas multi-turn, o caller
e responsavel por concatenar a historia em `messages` antes de chamar
`run()`. Veja [passo 8 — `HistoryWindow`](08_opcionais_history_window.md)
para a regra de truncagem padrao.

---

## Cuidados

- `fanout` agents sao forcados a `exposed_to_user=False` pela fabrica
  (com `WARNING` no log se o YAML tiver declarado o contrario). Personas
  do ensemble sao internas por definicao.
- Coordinator NAO precisa de `output_schema`; sua saida e texto livre.
  Se voce declarar um schema mesmo assim, `run()` retorna
  `model_dump_json()` em vez de `str(...)`.
- Cost guard: cada `network.run` emite um log estruturado com tempo total e
  contagem de successos/falhas. Util para alarmar quando timeouts sobem
  (sinal de model degradation ou prompt bloated).

## Exemplo executavel

Veja [`docs/examples/multiagent/ensemble/`](../examples/multiagent/ensemble/)
para um exemplo end-to-end (3 personas + coordenador) que roda sem
credenciais (usa stub do `Runner.run`, mesma tecnica do
`tests/multiagent/conftest.py`).

## Referencias

- [Issue #150](https://github.com/BeMonkAI/atendentepro/issues/150) — `ParallelNetwork`
- [Issue #151](https://github.com/BeMonkAI/atendentepro/issues/151) — YAML wiring + service dispatch
- [`atendentepro/multiagent/parallel.py`](../../atendentepro/multiagent/parallel.py) — implementacao
- [Passo 12 — hierarquia (`call_agent`)](12_opcionais_multiagent_hierarquia.md)
