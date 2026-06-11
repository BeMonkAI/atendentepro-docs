# Passo 24 (opcional): Verificador de Fundamentação (output-side groundedness)

> **Code:** `GroundednessVerifier` (`atendentepro/verification/groundedness_verifier.py`).
> **Status:** opt-in (v0.52.0). Renomeado a partir de "output guardrail" /
> `OutputSpecialistGuardrail`. Roda apenas em **SHADOW** por padrão —
> loga o veredito e **nunca altera a resposta**. Nenhum tenant é afetado
> até ativar explicitamente. Hoje LIVE em shadow no tenant interno `ref`
> (deploy `atendentepro-server`).

## O que é

O **Verificador de Fundamentação** é a camada **output-side** do AtendentePro.
Depois que a resposta é gerada — e **antes** de ela ser persistida/enviada —
ele confere se a resposta está **fundamentada (grounded)** no contexto RAG
recuperado.

Glosa informal: *a trava que confere se a resposta está apoiada nos documentos
antes de enviar.*

> **Ele NÃO é um guardrail.** Guardrails (`SpecialistGuardrail`, Passo 22) são
> **input-side**: classificam a *mensagem que entra* (jailbreak / PII / fora de
> escopo) e decidem `allow|warn|escalate|block` **antes** de o LLM rodar. O
> Verificador é **output-side**: afere a *resposta já gerada* contra o contexto
> recuperado.
>
> **Mnemônica:** *Guardrails protegem a ENTRADA; o Verificador confere a SAÍDA
> antes de enviar.*

A fronteira de pacote (`guardrails/` vs `verification/`) é auditável via
`.importlinter` — não é só organização de pastas. O Verificador **reutiliza** o
contrato de veredito do specialist por economia DRY (`GroundednessVerdict` herda
de `SpecialistGuardrailVerdict`), mas **não é** um guardrail.

### Como funciona (cascata 3 tiers + gate)

- **Tier 0 — gate de elegibilidade + heurística ZERO-LLM (~2ms):** já-roteado?
  `ParallelNetwork`/`BaseNetwork` (sem `new_items`) → `not_applicable` /
  `detector_disabled=true`; sem RAG → escape-hatch; overlap léxico
  resposta×contexto abaixo do piso; claim factual (nº/data/preço/CNPJ) ausente
  do contexto. Saudação / handoff puro / sem-claim → `allow` direto (a maioria
  do tráfego nunca paga LLM — economia real da cascata).
- **Tier 1 — entailment (1 chamada LLM barata):** rotula cada afirmação
  `Supported | Insufficient | Contradicted` contra `go_to_rag.answer`;
  `faithfulness` reduzido por **MIN-over-claims** para claims de alto risco
  (anti-diluição). Só os suspeitos do Tier 0 são promovidos.
- **GATE — `load_groundedness_verifier_thresholds` + `apply`:** aplica os
  thresholds do YAML e emite o `decision`.

## Quando aplicar

Use este passo quando o tenant é **sequencial com RAG** e você quer **observar**
(em shadow) se as respostas estão fundamentadas no contexto recuperado — antes
de qualquer ação. Casos típicos:

1. Tenants regulados (saúde / financeiro / jurídico) onde uma resposta
   inventada ("alucinação") é caro.
2. Tenants com base de conhecimento volátil (preços/políticas que mudam) onde
   se quer um **sinal de auditoria** por turno.
3. Coleta de dados para calibração antes de eventualmente ligar o enforce (F4).

**Não aplique** em tenants `ParallelNetwork`/ensemble (consumidores
Path-B): o `BaseNetwork.run` só expõe a string final, então a camada se
auto-desabilita (`detector_disabled=true`) — **nunca** marca "faithful"
silencioso. Cobertura desses tenants é follow-up (expor `new_items` no
`BaseNetwork.run`).

---

## Como ATIVAR

O modo **SHADOW** é opt-in por tenant. Há três níveis de ativação (do mais
explícito ao global):

### 1. Via `setup()` do serviço (por tenant)

```python
manager.setup(
    client="ref",
    templates_root=Path("./client_templates"),
    groundedness_verifier_shadow=True,   # liga o shadow para este tenant
)
```

Isso seta a flag `state.groundedness_verifier_shadow` no `_TenantState`. A cada
turno, **após** produzir `assistant_text` e **antes** de
`session.messages.append`, o serviço dispara
`asyncio.create_task(_emit_groundedness_shadow(...))` — o usuário nunca espera.

### 2. Via variável de ambiente (kill-switch global)

```bash
ATENDENTEPRO_GROUNDEDNESS_VERIFIER_SHADOW=true
```

Liga o shadow para todos os tenants do processo (útil em deploy de referência
como `atendentepro-server`). Override de modelo/provider do juiz:

```bash
ATENDENTEPRO_GROUNDEDNESS_VERIFIER_MODEL=gpt-4o-mini
ATENDENTEPRO_GROUNDEDNESS_VERIFIER_TIMEOUT=1.5
```

### 3. Via YAML por tenant (thresholds)

`client_templates/<tenant>/groundedness_verifier_config.yaml`, top-key
`groundedness_verifier`:

```yaml
groundedness_verifier:
  enabled: true
  mode: shadow                       # shadow (default) | enforce (F4) — começar SEMPRE em shadow
  # --- modelo / provider do juiz (anti-self-preference) ---
  tier1_checker: llm-judge           # llm-judge (default) | hhem | minicheck (extra [output-nli])
  # --- thresholds de groundedness (Tier 1) ---
  faithfulness_high: 0.85            # >= => allow sem promover
  faithfulness_review: 0.60          # [review, high) => zona-cinza
  retrieval_confidence_floor: 0.45   # cosine médio do go_to_rag abaixo disso => suspeita (modo b)
  ground_floor: 0.50                 # piso de overlap léxico no Tier 0
  # --- thresholds de veredito (espelham SpecialistConfig) ---
  confidence_floor: 40               # confidence < => downgrade allow (NÃO block; fail-open output-side)
  escalate_if_risk_gte: high
  block_if_risk_gte: medium          # em shadow: apenas registrado
```

O loader `load_groundedness_verifier_thresholds` lê esse YAML; sem arquivo,
roda os defaults seguros.

### 4. Gating por agente (#441, opcional)

Por default o shadow dispara em **todo** turno sequential+RAG do tenant. Para
restringir a agentes específicos da rede (ex.: só respostas fundamentadas em
conhecimento, poupando latência/custo nos agentes transacionais), declare a
lista de display names:

```python
manager.setup(
    ...,
    groundedness_verifier_shadow=True,
    groundedness_verifier_agents=["Knowledge Agent", "Answer Agent"],
)
```

Ou no YAML por tenant (mesma chave, dentro do top-key `groundedness_verifier`):

```yaml
groundedness_verifier:
  groundedness_verifier_agents:
    - Knowledge Agent
    - Answer Agent
```

Semântica:

- **Ausente / `None`** → sem filtro, todo turno dispara (comportamento
  pré-#441, byte-for-byte).
- **Lista presente** → o shadow só dispara quando o `agent_name` extraído do
  run está na lista. O match é **normalizado** (mesmo contrato dos
  `agent_scopes` dos guardrails: case-insensitive, `-`/espaços equivalentes).
- **Lista vazia** → nunca dispara (alavanca explícita de desligar mantendo a
  flag shadow ligada).
- **Precedência explicit-wins (#408):** o valor passado no `/setup` vence o
  YAML; o YAML vence o default.
- Turno cujo `agent_name` não pôde ser extraído é **pulado** quando há filtro
  configurado (não dá para atribuí-lo a um agente permitido).
- Nomes desconhecidos não são validados contra a rede (redes custom têm nomes
  arbitrários); entradas não-string são dropadas com warning no load.

No caminho **stateless** (inline-config `/chat`, #391), que não tem
`_TenantState` por tenant, o filtro é um default de deployment:

```bash
ATENDENTEPRO_DEFAULT_GROUNDEDNESS_VERIFIER_AGENTS="Knowledge Agent, Answer Agent"
```

(comma-separated; vazio/ausente = sem filtro).

---

## API

Todos os símbolos públicos são importados via `from atendentepro import ...`
(nunca submódulo — respeitar `.importlinter`):

```python
from atendentepro import (
    run_groundedness_check,
    GroundednessVerdict,
    GroundednessVerifierConfig,
    load_groundedness_verifier_thresholds,
)
```

### Uso programático

```python
from pathlib import Path
from atendentepro import (
    run_groundedness_check,
    GroundednessVerdict,
    GroundednessVerifierConfig,
    load_groundedness_verifier_thresholds,
)

cfg: GroundednessVerifierConfig = load_groundedness_verifier_thresholds(
    templates_root=Path("./client_templates"),
    client="ref",
)

verdict: GroundednessVerdict = await run_groundedness_check(
    response_text="Funcionamos das 9h às 17h, de segunda a sexta.",
    message="Que horas vocês abrem?",
    retrieved_context="Horário de atendimento: 9h-17h, seg-sex.",
    retrieval_confidence=0.82,
    history=[],
    tool_results=[...],     # saída do go_to_rag / scheduling_tools / API
    cfg=cfg,
)

# Em SHADOW: apenas leia o veredito (NUNCA altera a resposta).
if verdict.decision == "allow":
    ...        # resposta fundamentada
elif verdict.decision == "warn":
    ...        # zona-cinza / Insufficient de baixo risco
elif verdict.decision == "escalate":
    ...        # contradição de alto risco / retrieval_confidence muito baixo
elif verdict.decision == "block":
    ...        # apenas registrado em shadow; enforce real é F4
```

### Campos do `GroundednessVerdict`

`GroundednessVerdict` estende `SpecialistGuardrailVerdict` (reuso DRY), mas
**não é** um guardrail.

| Campo | Tipo | Descrição |
|---|---|---|
| `decision` | `Literal["allow", "warn", "escalate", "block"]` | Veredito final. **4 vias — NÃO 5.** `ticket`/`abstain` **não existem no código** (aspiracionais, F4). |
| `risk_level` | `Literal["none", "low", "medium", "high", "critical"]` | Severidade da preocupação. |
| `category` | `str` | Tag de taxonomia (ex: `ungrounded_unverifiable`). |
| `confidence` | `int` (0..100) | Auto-relatada pelo modelo. |
| `reasoning` | `str` | Justificativa curta. |
| `error_mode` | `Literal["a", "b", "c", "none"]` | Modo de erro: (a) alucinação/sem suporte, (b) confiante-mas-errado, (c) incerteza, ou nenhum. Auditoria/calibração. |
| `b_routed_to_human` | `bool` | `True` quando (b)+alto-risco foi roteado a humano fora da curva de calibração. |
| `faithfulness` | `Optional[float]` | Score de fidelidade ao contexto (Tier 1). `None` se não chegou ao Tier 1. |
| `tier_reached` | `int` (0/1) | Tier máximo alcançado na cascata. |
| `detector_disabled` | `bool` | `True` quando a camada não pôde rodar (ex: `ParallelNetwork` sem `new_items`). Nunca "faithful" silencioso. |

### `GroundednessVerifierConfig`

`GroundednessVerifierConfig` (frozen) espelha o `SpecialistConfig` do guardrail
(`name`/`model`/`openai_client`/`block_if_risk_gte`/`escalate_if_risk_gte`/
`confidence_floor`) e adiciona os campos de groundedness:

| Campo | Default | Descrição |
|---|---|---|
| `faithfulness_high` | `0.85` | `faithfulness >= high` → `allow`. |
| `faithfulness_review` | `0.60` | `[review, high)` → zona-cinza. |
| `retrieval_confidence_floor` | `0.45` | cosine médio do `go_to_rag` abaixo disso → suspeita de doc-errado (modo b). |
| `ground_floor` | — | piso de overlap léxico (Tier 0). |
| `confidence_floor` | `30`/`40` | `confidence` < piso em `allow` → downgrade. **Fail-OPEN output-side: NÃO block.** |
| `block_if_risk_gte` | `None` | em shadow: apenas registrado. |
| `escalate_if_risk_gte` | `None` | promove a `escalate` quando `risk_level >= threshold`. |
| `tier1_checker` | `llm-judge` | `llm-judge` (default) \| `hhem` \| `minicheck` (extra `[output-nli]`). |

`build_entailment_judge_agent` (também público) clona `build_specialist_agent`
e configura o `openai_client` **por-Agent** (anti-race), nunca via
`set_default_openai_client`.

---

## Modo SHADOW e como ler os vereditos

Em **shadow** a camada **nunca altera a resposta**: ela apenas loga o veredito.
O logger dedicado é:

```python
import logging
logging.getLogger("atendentepro.service.groundedness_verifier")
```

Cada turno emite um registro estruturado com, no mínimo:
`{faithfulness, tier_reached, claims_flagged (Supported/Insufficient/Contradicted),
error_mode, retrieval_confidence, decision, b_routed_to_human, latency_ms,
detector_disabled}`.

Para inspecionar os vereditos, capture esse logger (handler/arquivo) e amostre
turnos. **Inclui explicitamente** turnos `ParallelNetwork` (`detector_disabled`)
e high-risk non-RAG (scheduling/API) — para o holdout não enviesar só para o
caminho sequential-RAG-feliz.

### Fail-policy (oposta ao guardrail)

| Camada | Direção | Fail-policy |
|---|---|---|
| `SpecialistGuardrail` | INPUT | **fail-CLOSED**: `except → block` (bloquear mensagem suspeita é seguro) |
| `GroundednessVerifier` | OUTPUT | **fail-OPEN em shadow**: `except → log`; nunca descarta uma resposta boa já gerada |

O fail-closed do guardrail é seguro para a entrada, mas seria **destrutivo** na
saída (descartaria um draft bom). Por isso o output-side é fail-OPEN.

---

## Escopo honesto (sempre incluir em comunicação)

O Verificador afere **FUNDAMENTAÇÃO no contexto recuperado**, **não verdade
absoluta**. Formalmente:

> `groundedness ≠ verdade`

Por isso o verbo é **verificar** (propriedade objetiva: "está apoiado no
contexto?") e **não validar** (chancela de verdade).

Implicações:

- **(a) Alucinação / claim sem suporte no RAG:** cobertura **forte** — é o caso
  principal.
- **(b) Confiante-mas-errado (closed-book):** cobertura **parcial e honesta** —
  só quando o próprio contexto RAG **contradiz** a resposta. "Confiante-mas-errado
  **fora** do RAG" é **estruturalmente indetectável** (API fechada, multi-provider,
  sem white-box probes; `top_logprobs` nunca é plumbado na lib). (b)+alto-risco
  vai **sempre a humano**, fora da curva (`b_routed_to_human=true`).
- **(c) Incerteza / baixa confiança:** cobertura via Tier 0 + Tier 1.

A camada **nunca** afirma "isto é verdade" — só "isto está/não está fundamentado
no contexto". **Não vender** detecção de (b) closed-book ao cliente.

### Decisão: 4 vias, NÃO 5

O `decision` enviado é `Literal["allow", "warn", "escalate", "block"]`
(herdado de `SpecialistGuardrailVerdict`). **Não existe `abstain` nem `ticket`
no código** — o "roteamento de 5 vias" dos documentos de design é
**aspiracional (F4)**. Documentos de comunicação e e-mails ao cliente **não
devem prometer as 5 vias**.

### Enforce é F4 (futuro)

Hoje a camada só roda em **shadow** (observa e loga). O modo **enforce** (agir:
anexar disclaimer, segurar a resposta, escalar a humano via Escalation Agent /
abrir ticket via Feedback Agent, com fallback programático) é **F4** — só liga
por-tenant onde houver calibration set rotulado + `require_distinct_judge`
satisfeito + circuit-breaker calibrado.

---

## Referências

- Conceito canônico (tom/mnemônica): `docs/conceitos/verificador-vs-guardrail.md`
- Guardrail input-side (irmão): `docs/setup_passo_a_passo/22_opcionais_specialist_guardrail.md`
- Design (reframado): `docs/plans/2026-06-01-output-side-wrong-answer-predictor-design.md`
- Rename design: `docs/plans/2026-06-02-rename-output-guardrail-to-groundedness-verifier-design.md`
- Módulo: `atendentepro/verification/groundedness_verifier.py`

## Confiança por logprobs (F-LP1, opt-in)

Com `logprobs_enabled: true` no `groundedness_verifier_config.yaml`, a chamada
Tier 1 que já existe passa a capturar o log-probability do token de label de
cada claim. Um claim `Supported` cujo label saiu com probabilidade abaixo de
`judge_confidence_floor` (default 0.6) é tratado como `Insufficient` — o sinal
só endurece o verdict, nunca aprova. Campos novos no shadow log:
`judge_confidence` (mínimo entre os claims) e `logprobs_available` (False
quando o provider não retorna logprobs — o comportamento volta ao padrão,
fail-open). Custo LLM extra: zero.

```yaml
groundedness_verifier:
  logprobs_enabled: true
  judge_confidence_floor: 0.6
```

## Probe closed-book p(true) (F-LP2, opt-in)

Com `closed_book_probe: true`, um draft SEM contexto recuperado que não é
cortesia nem claim numérico (esses já geram `warn` no Tier 0) dispara uma
chamada de 1 token que pergunta ao modelo julgador se a afirmação é
verdadeira e lê o log-probability da resposta. `p_true` abaixo de
`p_true_floor` (default 0.55) gera `warn` (`escalate` se casar
`high_stakes_patterns`). É o primeiro ataque ao residual closed-book
qualitativo (#422); o teto groundedness ≠ verdade permanece — p(true) é
self-evaluation, não verificação externa. Timeout herdado de
`tier2_timeout_s` — atenção: reduzir `tier2_timeout_s` para acelerar o Tier 2
também corta o budget do probe (é o mesmo knob para os dois). Falha do probe
nunca bloqueia (fail-open).

```yaml
groundedness_verifier:
  closed_book_probe: true
  p_true_floor: 0.55
```

## Logprobs do gerador (F-LP3, opt-in, duplo gate)

Dois gates independentes: (1) env `ATENDENTEPRO_GENERATOR_LOGPROBS=1` no deploy
envolve o client global com captura de logprobs (toca o caminho quente de
geração — ligar com parcimônia); (2) `generator_logprobs: true` no YAML do
tenant consome o sinal. Quando ambos ligados, um claim numérico cujo pior
token saiu com logprob abaixo de `gen_min_logprob_floor` (default −4.0) é
promovido ao Tier 1 mesmo que o token-presence o considere fundamentado. O
sinal é best-effort sob concorrência (documentado no código) e só promove —
nunca aprova. O gate de env é reavaliado apenas na próxima construção do
client: alternar `ATENDENTEPRO_GENERATOR_LOGPROBS` em runtime exige chamar
`clear_client_cache()` (ou reiniciar o processo).

```yaml
groundedness_verifier:
  generator_logprobs: true
  gen_min_logprob_floor: -4.0
```


## Ancoragem numérica canônica + teto de plausibilidade (#455, opt-in)

### Ancoragem numérica canônica (`canonical_numeric_match`)

Por padrão, o Tier 0 verifica claims numéricos por presença literal de tokens
no contexto ("R$ 1.234,56" não ancora em "1234.56 BRL" mesmo que sejam o mesmo
valor). O flag `canonical_numeric_match: true` ativa uma comparação por **valor
canônico**: formatos pt-BR e US são normalizados, o `+` inicial é descartado, o
`-` é preservado (uma inversão de sinal permanece não-fundamentada), e o `%` não
faz parte do valor (50% ancora em 50). Zeros decimais finais são removidos
(`10,0 ≡ 10`).

**Tiny-int exemption:** tokens inteiros 0–99 sem decimal, sinal ou `%` são
isentos da verificação (prosa como "13 semanas" não dispara promoção ao Tier 1).

**Invariante monotone:** este flag só melhora a precisão do sinal do gate (um
valor presente-mas-formatado-diferente agora ancora). Nunca afrouxa a detecção
de inversão de sinal — `-12%` vs `12%` continua sendo uma claim não-fundamentada
com o flag ligado.

```yaml
groundedness_verifier:
  canonical_numeric_match: true
```

### Teto de plausibilidade (`value_ceilings` / `bounds_provider`)

Complementar ao Tier 0 (que verifica *se* o valor está no contexto), o check de
plausibilidade verifica *se o valor faz sentido* dado o que o tenant sabe sobre
o domínio. Um valor fundamentado-mas-impossível (ex: uma marca com teto de vendas
de R$ 1 M reportando R$ 1,17 bilhão) é escalado imediatamente, com
`category="implausible_magnitude"`, `error_mode="b"` (grounded-but-wrong),
`tier=0`.

**Semântica conservadora (fail-open):**
- Se não houver claim com palavra de magnitude (mil/mi/bi/milhão/bilhão) na
  resposta → passa (sem número para verificar).
- Se nenhuma chave de entidade aparecer na resposta → passa (escopo não
  identificado).
- Quando múltiplas entidades correspondem, usa-se o **teto máximo** (o maior
  valor plausível); o claim só falha se exceder até esse máximo multiplicado
  pelo `plausibility_margin`.
- `plausibility_margin` (default 2.0) define a folga: um claim de R$ 1,9 bi
  com teto R$ 1 M e margem 2.0 → 1,9 bi > 1 M × 2 → escalado.

**Quem deve calcular os tetos?** A lib apenas consome o mapeamento; derivar
tetos a partir dos dados do tenant (ex: volume histórico máximo) é
responsabilidade do consumidor.

**`bounds_provider`:** alternativa code-only (não configurável via YAML) que
aceita uma callable `(entity_normalised: str) -> Optional[float]`. Tem
precedência sobre `value_ceilings` quando ambos estão presentes.

```yaml
groundedness_verifier:
  canonical_numeric_match: true
  plausibility_margin: 2.0
  value_ceilings:
    marca alpha: 1000000
```

> **Resposta correta nunca degrada:** um valor fundamentado e plausível passa
> pelo check sem custo adicional. O check só escalona o impossível.
