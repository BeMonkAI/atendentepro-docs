# Passo 10 (opcional): guardrails preflight (`run_input_guardrails`)

> **Issue:** [#122 — guardrails.run_input_guardrails should accept conversation history](https://github.com/BeMonkAI/atendentepro/issues/122)

## Quando aplicar

Use este passo quando a aplicação:

- precisa **validar mensagens antes de invocar o agente** (ex.: hub multi-canal que recusa input cedo, sem custo de orquestração);
- substitui o LLM scope validator por heurístico próprio (keyword/regex, por custo ou latência) e quer reusar as outras camadas (jailbreak, custom `hard_block_patterns`, escalation bypass) sem fork do módulo;
- está pisando no falso-positivo de short follow-ups (`"sim"`, `"ok"`, `"1"`, `"esse"`) em scope check próprio, descrito em [Passo 7 § Guardrail de escopo: cuidado em multi-turn](07_cuidados_principais.md).

Não aplicar em chatbots que já usam apenas o pipeline do SDK (`Runner.run` com `@input_guardrail`) — o `run_input_guardrails` existe **paralelo** ao SDK, não substitui.

---

## API

```python
from atendentepro import run_input_guardrails, InputGuardrailDecision

decision: InputGuardrailDecision = await run_input_guardrails(
    "sim",
    agent_name="Knowledge Agent",          # default: "Triage Agent"
    history=[
        {"role": "user", "content": "quero um reporte"},
        {"role": "assistant", "content": "Voce quis dizer Deep-Dive de Marca?"},
    ],
    templates_root=Path("./client_templates"),
    template_name="meu_cliente",
    model=None,                            # opcional, override do scope agent
    provider_name=None,                    # opcional ("openai", "deepseek", ...)
    use_scope_validator=True,              # False = pula camada 4
)
if decision.blocked:
    print(decision.layer, decision.message)
```

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `message` | `str` | — | A mensagem do turno atual a validar. |
| `agent_name` | `str` | `"Triage Agent"` | Agente cujo escopo se aplica (`"Knowledge Agent"`, `"Flow Agent"`, etc.). |
| `history` | `list[dict] \| None` | `None` | Histórico prévio (`{"role", "content"}`). Renderizado como transcript role-tagged para o LLM scope validator. |
| `templates_root` | `Path \| None` | `None` | Raiz dos templates. `None` cai no que foi setado via `load_guardrail_config`. |
| `template_name` | `str \| None` | `None` | Cliente / template ativo. |
| `model` | `Any` | `None` | Override de modelo do scope validator. |
| `provider_name` | `str \| None` | `None` | Provider para detecção de capabilities. |
| `use_scope_validator` | `bool` | `True` | `False` pula a camada 4 (LLM scope) — útil quando o cliente tem heurístico próprio. |

**Retorno:** `InputGuardrailDecision`

| Campo | Tipo | Descrição |
|---|---|---|
| `blocked` | `bool` | `True` quando a mensagem foi rejeitada por alguma camada. |
| `layer` | `str` | Camada que decidiu. Valores: `"allowed"`, `"hard_block"`, `"custom_hard_block"`, `"escalation_bypass"`, `"scope_in"`, `"scope_out"`. |
| `message` | `str \| None` | Mensagem para o usuário (custom hard_block) ou `reasoning` do scope validator. |

---

## Exemplo 1 — preflight antes do `Runner.run`

```python
from atendentepro import run_input_guardrails, run_with_history

decision = await run_input_guardrails(user_msg, history=history, agent_name="Triage Agent")
if decision.blocked:
    if decision.layer == "custom_hard_block":
        # PII bloqueada (ex.: CPF) — surface message com a mensagem custom
        return {"reply": decision.message}
    return {"reply": "Não posso ajudar com isso. Reformule, por favor."}

result, history = await run_with_history(
    network, network.triage,
    messages=[{"role": "user", "content": user_msg}],
    history=history,
)
return {"reply": result.final_output, "history": history}
```

---

## Exemplo 2 — heurístico próprio + camadas 1-3 da lib

Casos típicos: cliente quer scope check com latência **sub-ms** (keyword/regex) mas não quer reescrever jailbreak hard-block, custom `hard_block_patterns` e escalation bypass.

```python
from atendentepro import run_input_guardrails

decision = await run_input_guardrails(
    user_msg,
    history=history,
    agent_name="Knowledge Agent",
    template_name="meu_cliente",
    use_scope_validator=False,      # <-- pula a camada LLM
)
if decision.blocked:
    return {"reply": decision.message or "Bloqueado por política."}

# Daqui pra frente, o cliente roda seu próprio scope check (heurístico)
if not minha_heuristica_scope(user_msg, history=history):
    return {"reply": "Fora do escopo."}

# Tudo passou — segue para Runner.run
```

A heurística do cliente fica responsável pelos follow-ups curtos (ver [Passo 7](07_cuidados_principais.md)).

---

## Como o histórico vira prompt

`run_input_guardrails` renderiza `history + [message]` como transcript role-tagged:

```
User: quero um reporte
Assistant: Voce quis dizer Deep-Dive de Marca?
User: sim
```

O LLM scope validator (camada 4) recebe esse texto e — pela regra 2 das suas instruções — aceita follow-ups neutros (`"sim"`, `"ok"`, `"1"`, `"esse"`) como dentro do escopo, porque vê o contexto da pergunta anterior. Sem essa renderização, o validador veria só `"sim"` e poderia rejeitar (latência ~500ms desperdiçada).

---

## Diferença entre os dois caminhos

| | SDK pipeline (`@input_guardrail`) | Standalone (`run_input_guardrails`) |
|---|---|---|
| Trigger | `Runner.run` automático | Caller invoca explicitamente |
| Input | SDK passa o input do agente | Caller passa `(message, history)` |
| Layers | 1-2 sem prompt role-tagged | 1-2 com prompt role-tagged |
| Output | `GuardrailFunctionOutput` (tripwire) | `InputGuardrailDecision` (estruturado) |
| Quando usar | Pipeline padrão | Preflight, heurístico custom, multi-canal |

Ambos compartilham a mesma layer chain interna (`_run_input_layers`) — comportamento equivalente em jailbreak, custom hard_block e escalation bypass.

---

## Limitações conhecidas

- O LLM scope validator é re-instanciado a cada chamada de `run_input_guardrails` (sem cache). Para alta cardinalidade de turnos, prefira `use_scope_validator=False` + heurístico no caller, ou use o pipeline do SDK que tem cache TTL (`get_guardrails_for_agent`).
- Não há retry / circuit-breaker — falha do LLM cai em fail-open (`scope_in`) com WARNING no log.

---

## Referências

- API pública: `from atendentepro import run_input_guardrails, InputGuardrailDecision`
- Implementação: `atendentepro/guardrails/manager.py::run_input_guardrails`
- Layer chain compartilhada: `atendentepro/guardrails/manager.py::_run_input_layers`
- Testes: `tests/test_guardrails_run_input.py`
- Issue: [#122](https://github.com/BeMonkAI/atendentepro/issues/122)
