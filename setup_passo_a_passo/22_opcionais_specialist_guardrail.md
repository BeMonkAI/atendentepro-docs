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
e vai em cada linha de shadow, para que uma medição antiga continue interpretável. O hash cobre
também o enquadramento do `state` enviado ao modelo (`STATE_FORMAT`: cabeçalhos, formato do turno,
separador e nome da pergunta, #536), então trocar um cabeçalho move a versão como trocar uma regra.
`assert_payload_covers_policy` reprova quando o payload perde, ganha ou reescreve uma regra.

## Shadow com motor tipado (#529)

> Para usar o JEV como camada que **decide** injection e escopo na entrada (não só em shadow), ver o [passo 29](29_opcionais_typed_input.md).

O shadow do especialista pode rodar o braço tipado (`choice` sobre as regras transcritas,
seção acima) ao lado do motor em produção, para comparar motores em tráfego real. O default não muda:
sem escolha, o shadow roda o próprio especialista.

| onde | chave | valores |
|---|---|---|
| `/setup` (por tenant) | `specialist_shadow_engine` | `specialist` (default), `jev_choice` |
| stateless (deploy) | env `ATENDENTEPRO_DEFAULT_SPECIALIST_SHADOW_ENGINE` | idem; valor desconhecido derruba o startup |
| credencial | env `ATENDENTEPRO_TYPED_API_KEY` (fallback `TYPESAFE_API_KEY`) | obrigatória para `jev_choice` |
| endpoint | env `ATENDENTEPRO_TYPED_ENDPOINT` | qualquer endpoint System One; default TypeSafe (ver [passo 29, seção 4.1](29_opcionais_typed_input.md)) |
| modelo | env `ATENDENTEPRO_TYPED_SHADOW_MODEL`, senão `ATENDENTEPRO_TYPED_MODEL` | default pinado `jev-1.13.0` (nunca `jev-latest`, que se move) |

A linha `specialist_shadow_verdict` ganha `engine` nos dois motores. No `jev_choice` ela traz
também `payload_version`, `model` e `probabilities` (distribuição por regra), `category` é a
regra escolhida (`rule_N`) e `confidence` é `max(probabilities)` em 0 a 100. O gating é o mesmo
para os dois motores: flag do tenant, scope e kill-switch `ATENDENTEPRO_SHADOW_SPECIALIST=0`.
Falha do braço tipado (sem chave, HTTP, opção desconhecida) vira linha `specialist_shadow_error`
com `engine`, e nunca afeta a resposta. Opção desconhecida é checada em TODAS as opções devolvidas,
não só na mais provável (#538); empate vai para a regra que vem antes na política, como o próprio
payload instrui. `tests/eval/guardrail_specialist/pilot_analysis.py` separa as linhas por `engine`
e gera uma seção por motor (#535); o gate de "≥ 10 disparos de PII" vale só para o especialista,
porque o braço tipado reporta `rule_N`.

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

### Sinais para o playbook aprendido (#596)

O refletor offline que escreve o `learned_playbook.yaml` (#594, página 30) lê duas coisas,
ambas pela `turn_id`.

**Sinais implícitos, opt-in.** Com `ATENDENTEPRO_TURN_SIGNALS=1` no deploy, a linha
`turn_outcome` ganha dez booleanos e uma lista de códigos calculados com o que o serviço já tem:

| Campo | Verdadeiro quando |
|---|---|
| `escalated` | o turno terminou no `Escalation Agent` ou chamou `registrar_escalacao` |
| `out_of_scope` | o tripwire do guardrail de entrada disparou (`no_reply_reason = out_of_scope`) |
| `repeated_question` | a mensagem atual é igual à mensagem anterior do usuário (sem diferença de caixa, espaço e `?!.` no fim). No stateless vale o `history` enviado pelo caller; no legado, a sessão |
| `complaint_ticket` | o `criar_ticket` do Feedback Agent foi chamado com `tipo = reclamacao` |
| `learnable` | `false` sempre que `out_of_scope` é `true`: turno fora do escopo NUNCA vira lição |
| `tool_error` | alguma tool levantou exceção (texto padrão do SDK) ou a tool http devolveu `status` `error`/`http_error` (#607) |
| `tool_args_invalid` | o SDK rejeitou os argumentos que o modelo mandou para uma tool (`Invalid JSON input for tool`) |
| `tool_missing_caller_auth` | uma tool `auth: caller` foi chamada sem `tool_auth` na request |
| `tool_repeated_same_args` | a mesma tool foi chamada duas vezes no turno com os mesmos argumentos (ordem das chaves não conta) |
| `tool_then_escalated` | o turno escalou depois de chamar alguma tool que não é a própria `registrar_escalacao` |
| `tool_error_codes` | lista (não booleano): códigos de erro do turno, ordenados e sem repetição: `raised`, `http_error` ou o `error` da resposta JSON da tool. Separa erro evitável (`invalid_format`) de resposta esperada (`not_found`). Código fora de `[a-z0-9_]{1,40}` vira `other`, porque o campo vem da tool e pode trazer texto livre (#614) |

Sem a variável (ou com qualquer valor diferente de `1`) a linha fica idêntica byte a byte à
anterior. Os sinais são só booleanos: nenhum texto de mensagem, argumento ou saída de tool entra na linha.
Quantas vezes cada tool rodou já está em `tool_names` (uma entrada por chamada).

**Feedback explícito: `POST /feedback`.** Mesmo gate de autenticação do `/chat` (`x-api-key`
quando `ATENDENTEPRO_SERVICE_TOKEN` está setado) e mesmo rate limit.

```json
{"tenant_id": "acme", "turn_id": "<ChatResponse.turn_id>", "score": -1,
 "comment": "não resolveu", "session_id": "s1", "user_id": "u1"}
```

- `score` é obrigatório e inteiro em `{-1, 0, 1}` (ruim, neutro, bom); bool, decimal ou texto
  dão 422. `turn_id` é obrigatório. `comment`, `session_id` e `user_id` são opcionais.
- Responde `202 {"status": "accepted", "turn_id": "..."}` e grava uma linha `turn_feedback`
  no logger `atendentepro.service.turn_feedback`. O serviço não procura o turno: o feedback
  pode chegar depois que o turno saiu da memória, ou num réplica diferente.
- **LGPD:** o comentário é texto do usuário final. Só os primeiros 200 caracteres vão para o
  log (mesmo corte do `reasoning` das linhas de shadow), mais `comment_len` com o tamanho
  original. A lib não armazena nada além dessa linha.
- O endpoint não tem env gate: é aditivo, nada muda para quem não chama, e quem chama já está
  optando por mandar o feedback.

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
