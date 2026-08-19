# Passo 22 (opcional): SpecialistGuardrail (multi-dimensional input guardrail)

> **Issue:** PR contendo F2/F3 do estudo `SpecialistGuardrail`.
> **Status:** opt-in (v0.41.0). O caminho padrão da lib em
> `atendentepro.guardrails.manager` continua usando o classificador
> binário; nenhum tenant existente é afetado até migrar explicitamente.

## Quando aplicar

Use este passo quando o tenant precisa de uma das três coisas que o
classificador binário **não consegue** expressar:

1. **Decisão `warn`** — declinar com elegância tópicos *borderline*
   (aconselhamento médico/legal/financeiro genérico) sem bloquear
   nem rotear para humano.
2. **Decisão `escalate` explícita** — rotear LGPD data-subject
   requests e pedidos "quero falar com humano" para um humano,
   sem precisar de heurística no Triage Agent.
3. **Output multi-dimensional** — UI / telemetria diferentes por
   `category` / `risk_level` (ex: dashboards de risco, tratamento
   por tipo de PII).

Se o tenant é um chatbot B2C simples cujo guardrail atual está com
métricas aceitáveis, **não migre**. O binary classifier custa menos
em tokens de instrução e tem menos surface área de prompt-tuning.

---

## API

```python
from atendentepro import (
    SpecialistConfig,
    SpecialistGuardrailVerdict,
    run_specialist_guardrail,
)

verdict: SpecialistGuardrailVerdict = await run_specialist_guardrail(
    "Quero falar com um atendente humano agora.",
    history=[
        {"role": "assistant", "content": "Posso ajudar com seu plano?"},
    ],
    cfg=SpecialistConfig(),       # defaults seguros
    enable_tools=False,           # True liga detect_pii + classify_intent
)

if verdict.decision == "block":
    return verdict.user_message or "Não posso ajudar com isso."
if verdict.decision == "warn":
    # Responder com cuidado; sugerir profissional.
    ...
if verdict.decision == "escalate":
    # Rotear para fila humana.
    ...
# allow → seguir para o agent normalmente.
```

| Campo | Tipo | Descrição |
|---|---|---|
| `decision` | `Literal["allow", "warn", "escalate", "block"]` | Veredito final. |
| `risk_level` | `Literal["none", "low", "medium", "high", "critical"]` | Severidade da preocupação. |
| `category` | `str` | Tag de taxonomia (`jailbreak`, `pii_disclosure`, `off_topic_benign`, etc). |
| `confidence` | `int` (0..100) | Auto-relatada pelo modelo. |
| `reasoning` | `str` | Justificativa curta. |
| `user_message` | `Optional[str]` | Mensagem opcional pra superfície de usuário (apenas em `block`/`warn`). |

## SpecialistConfig

```python
@dataclass(frozen=True)
class SpecialistConfig:
    name: str = "Compliance Specialist"
    model: str = "gpt-4o-mini"
    persona: str = "..."
    scope: str = "Customer service ..."   # injetado no prompt
    block_if_risk_gte: Optional[RiskLevel] = None   # opt-in
    escalate_if_risk_gte: Optional[RiskLevel] = None # opt-in
    confidence_floor: int = 30
```

- **`block_if_risk_gte`**: quando definido, qualquer veredito com
  `risk_level >= threshold` é promovido para `block`. Padrão `None`
  = confiar no modelo. Use `"high"` para tenants regulados (saúde,
  financeiro) que preferem fail-closed.
- **`escalate_if_risk_gte`**: análogo para escalate. Padrão `None`
  porque promover automaticamente `critical → escalate` enviava
  jailbreaks para humano em vez de bloquear (regressão observada
  em v0 e corrigida em v0.1).
- **`confidence_floor`**: vereditos `allow` com confidence abaixo
  desse piso são rebaixados para `block` (com clarificação). Padrão
  `30` para que o ruído natural do modelo não vire UX ruim.

## Tools (opcional, `enable_tools=True`)

Quando ligado, o agente recebe duas function tools:

- **`detect_pii(text)`** — regex sweep determinístico para padrões
  brasileiros (CPF / RG / CNPJ / cartão validado por Luhn / e-mail /
  telefone BR / CEP / CID-10 / heurística "filha de N anos").
- **`classify_intent(text, history)`** — classifier coarse com
  retorno `{in_scope, escalate_human, off_topic, ambiguous,
  mixed_in_scope_and_handoff}`. Disambigua mensagens multi-intent.

**Resultado empírico em D1 v0.2 (100 itens):** tools não movem o
ponteiro além do prompt-only (90% vs. 91%, dentro de variance).
Use quando o tráfego do tenant tem alta cardinalidade de PII ou
multi-idioma — onde o prompt não consegue enumerar tudo.

## Backwards-compat

Para callers que esperam `is_in_scope: bool` do contrato binário:

```python
legacy = verdict.to_legacy()
if not legacy.is_in_scope:
    ...
```

`to_legacy()` mapeia `{allow, warn, escalate} → True` e `{block} → False`.

## Observações

- Layers 1-3 da chain canônica (`_HARD_BLOCKLIST` + custom regex +
  escalation bypass) **não são executadas** quando você chama
  `run_specialist_guardrail` diretamente. Se quiser defesa em
  profundidade, encadeie manualmente:

  ```python
  from atendentepro import run_input_guardrails

  pre = await run_input_guardrails(message, history=history)
  if pre.blocked:
      return pre  # regex já bloqueou
  verdict = await run_specialist_guardrail(message, history=history)
  ```

- O specialist usa `Runner.run` com `max_turns=2` (tool-free) ou
  `max_turns=6` (com tools). Você pode override via
  `run_specialist_guardrail(..., max_turns=...)`.

- Latência mediana em `gpt-4o-mini`: ~1.6s/turno. Para tenants com
  SLA mais apertado, considere `gpt-4o-mini-tts` ou caching de
  vereditos por hash do conteúdo (não implementado na v0.41.0).

## Referências

- Estudo completo: `docs/plans/2026-05-15-specialist-guardrail-study.md`
- Paper JAES: `docs/papers/specialist-guardrail/main.tex`
- Suite de avaliação + harness: `tests/eval/guardrail_specialist/`
- Reports D1 v0.2: `docs/plans/eval-*-d1v0.2.md`
