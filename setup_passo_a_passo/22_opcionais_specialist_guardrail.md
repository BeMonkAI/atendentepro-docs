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
| `category` | `str` | Tag de taxonomia (`jailbreak`, `pii_disclosure`, `off_topic_benign`, etc), **ou** uma categoria operacional (ver abaixo). |
| `confidence` | `int` (0..100) | Auto-relatada pelo modelo. |
| `reasoning` | `str` | Justificativa curta. |
| `user_message` | `Optional[str]` | Mensagem opcional pra superfície de usuário (apenas em `block`/`warn`). |

### Categorias operacionais (#509)

A camada é **fail-closed**: qualquer falha operacional devolve `block`, e isso
não mudou. O que mudou é que a falha passou a dizer **por quê**, em vez de
todas caírem em `ambiguous`, que é indistinguível de um bloqueio real por
conteúdo.

| `category` | Significa | Retry? |
|---|---|---|
| `parse_error` | O modelo respondeu sem JSON, duas vezes seguidas | sim, 1 vez |
| `timeout` | A chamada estourou o tempo | não |
| `provider_error` | Provider fora do ar, licença, tooling | não |

Estão em `OPERATIONAL_CATEGORIES`. **Elas não são vereditos sobre a
mensagem**: dizem que a camada não conseguiu chegar a um. Um dashboard de
risco deve filtrá-las para fora da contagem de bloqueios, senão uma queda de
provider aparece como pico de ataque.

Só o `parse_error` é re-tentado, e uma vez. A resposta sem JSON é
comprovadamente intermitente (a mesma mensagem reenviada parseia), então a
segunda chamada recupera um turno que bloquearia um cliente legítimo. Provider
caído e licença inválida não melhoram na segunda tentativa, e re-tentá-los
dobraria a espera do usuário num guardrail de entrada.

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

## Payload tipado: transcrição, não paráfrase (#531)

Quando o especialista roda contra um modelo tipado (braço `choice`), o conjunto de opções
**é a política**. Por isso as opções são geradas por código a partir das regras numeradas do
`SPECIALIST_PROMPT_TEMPLATE` (`atendentepro/guardrails/typed_payload.py`), nunca escritas à mão.

Medido no mesmo corpus, com o mesmo modelo pinado e a mesma decisão, mudando só o texto:

| opções | instrução | acurácia |
|---|---|---:|
| parafraseadas | redação A | 72% |
| parafraseadas | redação B | 76% |
| transcritas, curtas | redação B | 86% |
| transcritas, completas | redação B | 88% |

Paráfrase não é equivalente a transcrição: uma paráfrase que omitiu uma regra falhou
exatamente onde aquela regra se aplicaria.

`PAYLOAD_VERSION` (12 hex do SHA-256 do payload canônico) muda com qualquer palavra da política
e vai em cada linha de shadow, para que uma medição antiga continue interpretável.
`assert_payload_covers_policy` reprova quando o payload perde, ganha ou reescreve uma regra.

## Shadow com motor tipado (#529)

O shadow do especialista pode rodar o braço tipado (`choice` sobre as regras transcritas,
seção acima) ao lado do motor em produção, para comparar motores em tráfego real. O default não muda:
sem escolha, o shadow roda o próprio especialista.

| onde | chave | valores |
|---|---|---|
| `/setup` (por tenant) | `specialist_shadow_engine` | `specialist` (default), `jev_choice` |
| stateless (deploy) | env `ATENDENTEPRO_DEFAULT_SPECIALIST_SHADOW_ENGINE` | idem; valor desconhecido derruba o startup |
| credencial | env `TYPESAFE_API_KEY` | obrigatória para `jev_choice` |
| modelo | env `ATENDENTEPRO_TYPED_SHADOW_MODEL` | default pinado `jev-1.13.0` (nunca `jev-latest`, que se move) |

A linha `specialist_shadow_verdict` ganha `engine` nos dois motores. No `jev_choice` ela traz
também `payload_version`, `model` e `probabilities` (distribuição por regra), `category` é a
regra escolhida (`rule_N`) e `confidence` é `max(probabilities)` em 0 a 100. O gating é o mesmo
para os dois motores: flag do tenant, scope e kill-switch `ATENDENTEPRO_SHADOW_SPECIALIST=0`.
Falha do braço tipado (sem chave, HTTP, opção desconhecida) vira linha `specialist_shadow_error`
com `engine`, e nunca afeta a resposta.

O braço tipado não é OpenAI-compatível e não entra em `providers/`: é camada de decisão,
não de geração.

**LGPD: é um suboperador novo.** Com `jev_choice`, cada turno em shadow envia a mensagem do
usuário, o histórico e o escopo do tenant para `api.typesafe.ai`, um processador diferente do
provedor de LLM que o tenant já usa. Só ligue para um tenant com o DPA e a lista de
suboperadores dele cobrindo esse envio.

## Juntando o shadow com o desfecho do turno (#530)

Cada turno ganha um `turn_id` (32 hex). Ele aparece:

- em `ChatResponse.turn_id` e nos frames `done` / `error` do `/chat/stream`;
- nas linhas `specialist_shadow_*`;
- numa linha nova por turno, `turn_outcome`, no logger `atendentepro.service.turn_outcome`:
  `turn_id`, `tenant_id`, `session_id`, `agent_name`, `tool_names`, `tool_results`,
  `tool_errors` (saídas com o prefixo de erro do Agents SDK), `no_reply`, `no_reply_reason`,
  `blocked` (tripwire de guardrail) e `error` (`max_turns_exceeded`, o motivo do frame `error`
  do stream, ou o nome da exceção de um turno que falhou; `null` num turno limpo). Nenhum texto
  de mensagem.

Turno que falha também emite `turn_outcome`: são justamente os turnos que não concluíram a
tarefa, e descartá-los enviesaria a junção para os que deram certo. Desconexão do cliente no
meio do stream não conta como falha.

**Onde fica o sink.** No pipeline de log do deploy, dentro da fronteira do tenant: as mensagens
são dado de cliente e só agregado sai de lá. A lib não guarda mensagem nem define retenção.

**A medição que isto destrava, sem rótulo.** Os turnos que concluíram a tarefa (a tool retornou
sem erro; no modo stateless, o caller confirma pela `turn_id` que persistiu o
`pending_client_persist`) são in-scope por comportamento observado. Qualquer bloqueio do shadow
nesses turnos é falso positivo. Junte as duas linhas pela `turn_id`.

**O que isto NÃO mede.** Recall: ataque é raro em produção, e minerar o que o guardrail atual
pegou daria positivos selecionados pela própria coisa avaliada. Nem o contrafactual dos turnos
bloqueados: o shadow diz o que o outro motor teria decidido, não se bloquear estava certo.

## Referências

- Estudo completo: `docs/plans/2026-05-15-specialist-guardrail-study.md`
- Paper JAES: `docs/papers/specialist-guardrail/main.tex`
- Suite de avaliação + harness: `tests/eval/guardrail_specialist/`
- Reports D1 v0.2: `docs/plans/eval-*-d1v0.2.md`
