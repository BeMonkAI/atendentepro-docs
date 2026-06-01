# 21 — Long-term memory cross-session: padrao canonico end-to-end

Issue [#273](https://github.com/BeMonkAI/atendentepro/issues/273) — guia consolidado para clientes que rodam memoria cross-session no AtendentePro. Reune as duas primitivas da lib (`memory_context_block_tag` em [doc 19](19_opcionais_memory_context_block_tag.md), `context_injection` em [doc 20](20_opcionais_context_injection.md)) com o **padrao Rule 0 hibrida** validado em prod (Marketing Insights Nestle, engine#196/#197) e o set completo de anti-patterns que cliente descobriu empiricamente.

Leia este documento ANTES de implementar memoria de longo prazo. Os 3 docs sao complementares:

- **Doc 19 — `memory_context_block_tag`**: instrui TODOS os agentes a CONSUMIR um bloco da conversa.
- **Doc 20 — `context_injection`**: ADICIONA o bloco ao payload de cada request.
- **Doc 21 (este) — Padrao canonico**: PROMPTS dos agentes (Triage Rule 0 + downstream), anti-patterns, wiring com `MemoryService.recall` + dedup.

> Numeracao do arquivo (21) difere do `08` sugerido na issue porque os slots 08-18 estao todos ocupados. O conteudo segue a especificacao do #273.

## 21.1 — Formato canonico do bloco

```
<long_term_memory>
- 2026-04-12: User X explicou que prefere relatorios em PDF.
- 2026-04-28: Tema "performance Q1" foi discutido — User pediu cortes em
  marketing digital.
- 2026-05-03: Decisao sobre fornecedor Y adiada para Q3.
</long_term_memory>
```

Convencoes obrigatorias:

1. **Tag XML literal** (`<long_term_memory>...</long_term_memory>` por default). Use a mesma tag em todos os lugares — generators, prompts, `memory_context_block_tag`. Drift de nome = bloco invisivel para o agente.
2. **Linha por fato.** Cada linha comeca com `- ` (markdown list item). LLMs tem alta confiabilidade lendo listas curtas.
3. **Prefixo temporal** (`YYYY-MM-DD: ` ou `Sessao YYYY-MM-DD: `) quando relevante para o cliente. Sem isso o agente perde sense de recencia.
4. **Truncar antes de injetar.** Cap em ~3-5 fatos / ~3000 chars. Memoria longa demais polui contexto e custa tokens. Cliente decide via `recall_limit` + dedup.
5. **Bloco vazio NAO deve ser injetado.** Se nao ha facts, NAO emitir `<long_term_memory></long_term_memory>`. Bloco vazio confunde o agente — ele tende a comentar a ausencia. Em vez disso, passar `context_injection=None` ou `[]`.

## 21.2 — Triage Rule 0: cobertura hibrida (meta puro + hibrido)

Memoria so ajuda se o Triage roteia corretamente quando o usuario PEDE para revisitar conversas passadas. Padrao Rule 0 cobre 2 casos:

### Tipo A — Meta puro
Usuario fala explicitamente sobre conversas passadas: *"O que ja conversamos?"*, *"Resuma o que combinamos"*, *"Voltando ao que falamos sessao passada"*.

### Tipo B — Hibrido (topico + verbo de comunicacao passada + referencia temporal)
Usuario menciona um topico e usa verbo no passado: *"Sobre o fornecedor Y que decidimos semana passada..."*, *"O relatorio que pedi mes passado..."*.

A regra Triage **DEVE** detectar ambos os tipos e nao confundir Tipo B com pergunta direta sobre o topico atual.

### Prompt sugerido para `triage_config.yaml::custom_prompt_prefix` ou `triage_custom_prompt_prefix`

```text
## Regra 0 — Memoria de sessoes anteriores

Antes de qualquer roteamento, verifique se a mensagem do usuario e:

(A) META PURO sobre conversas passadas — exemplos:
    - "O que ja conversamos?"
    - "Resuma o que combinamos ate aqui"
    - "Lembra do que decidimos na ultima sessao?"

(B) HIBRIDO — topico + verbo de comunicacao no passado + referencia temporal:
    - "Sobre o fornecedor X que combinamos semana passada..."
    - "O relatorio que pedi mes passado..."
    - "Voltando ao tema Y que ja conversamos..."

Em ambos os casos, NAO faca handoff. Responda voce mesmo usando o bloco
`<long_term_memory>` que pode estar presente como mensagem de sistema.

LOGICA:
1. Se ha bloco `<long_term_memory>` no contexto: resuma os fatos relevantes
   ao topico mencionado (ou todos, no caso (A)).
2. Se o bloco esta ausente OU o topico solicitado nao aparece no bloco:
   responda **"Nao tenho registro sobre <topico>"** (Tipo B) ou
   **"Nao tenho registro de conversas anteriores"** (Tipo A).
3. NUNCA diga "nao houve" ou "nao discutimos" sem checar o bloco. Se nao
   checou, o status correto e "nao tenho registro" — diferente de negar
   que aconteceu.
```

A distincao **"nao tenho registro"** vs **"nao houve"** e crucial: a primeira admite incerteza epistemica (o bloco pode estar truncado ou faltar), a segunda afirma falsamente que o evento nao ocorreu.

## 21.3 — Instrucao para agentes downstream (Flow, Answer, Knowledge, Interview)

Quando o usuario nao esta em modo meta-conversa, ele faz uma pergunta direta — mas o agente downstream ainda pode usar o bloco como **contexto silencioso** para enriquecer a resposta.

A lib v0.39.0+ resolve isso automaticamente quando `memory_context_block_tag="long_term_memory"` esta setado em `create_*_network` (ver [doc 19](19_opcionais_memory_context_block_tag.md)). O bloco abaixo e adicionado a TODOS os agentes da rede:

```text
## MEMÓRIA DE SESSÕES ANTERIORES
Se houver um bloco `<long_term_memory>...</long_term_memory>` no contexto
da conversa (como mensagem de sistema), use o conteudo dele para enriquecer
sua resposta com fatos persistentes que o usuario compartilhou em sessoes
passadas.

Regras:
- NAO mencione literalmente o bloco nem suas tags na resposta — use o
  conteudo apenas como contexto silencioso.
- A regra anti-alucinacao numerica continua valendo: so cite numeros que
  vieram de `tool_outputs` da sessao atual, NUNCA de memoria.
- Quando o bloco estiver ausente, opere normalmente sem comentar a
  ausencia.
```

### Tres invariantes para agentes downstream

1. **Verificar o bloco ANTES de chamar tool**, se a pergunta tem hint temporal. Exemplo: usuario pergunta *"qual foi o budget Q1?"*. Se ha `- 2026-03-15: Budget Q1 aprovado em R$ 250k.` no bloco, usar como contexto. Mas a resposta numerica final deve vir de `tool_outputs` da sessao atual, NUNCA do bloco.
2. **Usar como contexto, nao como output.** Frase "como combinado na sessao passada" e ok. Citar literalmente "<long_term_memory>" ou "no bloco de memoria" e quebra de invariante.
3. **Quando bloco ausente, operar normalmente.** Nao comentar a ausencia ("nao tenho acesso a memoria..."). Apenas responder a pergunta atual.

## 21.4 — Anti-patterns que sao bugs em prod

Cada item abaixo foi capturado em deployments reais. Audite o cliente contra esta lista.

### Anti-pattern 1: "Nao houve" sem checar

**Sintoma:** usuario pergunta *"o que combinamos sobre fornecedor X?"*, agente responde *"Nao houve discussao sobre fornecedor X nesta conversa"* — mesmo havendo `- 2026-04-28: User aprovou fornecedor X.` no bloco.

**Causa:** Triage roteou para o agente errado OU o agente nao tem instrucao para ler o bloco.

**Fix:** Rule 0 do Triage + `memory_context_block_tag` para garantir downstream.

### Anti-pattern 2: Confundir memoria com tool_outputs (alucinacao numerica)

**Sintoma:** Bloco diz `- Budget Q1 R$ 250k`. Tool atual retorna `budget_q2: R$ 180k`. Agente responde *"Q1 foi R$ 250k e Q2 R$ 180k"* — citando numero de memoria.

**Causa:** Falta da regra anti-alucinacao "so numeros de tool_outputs" no prompt do agente.

**Fix:** Instrucao explicita: "Numeros sao SEMPRE da sessao atual via tool_outputs. Memoria e contexto, nao fonte de numeros." A lib v0.39.0+ ja injeta isso via `memory_context_block_tag`.

### Anti-pattern 3: Mencionar literalmente o bloco

**Sintoma:** Resposta inclui "Segundo o `<long_term_memory>` que recebi..." ou "Nos meus registros de memoria..."

**Causa:** Falta da regra "NAO mencione literalmente o bloco" no prompt.

**Fix:** Doc 19 ja gera essa instrucao. Se cliente sobrescreveu `custom_prompt_*` e perdeu a injecao, restaurar.

### Anti-pattern 4: Bloco vazio injetado

**Sintoma:** Cliente injeta `<long_term_memory></long_term_memory>` quando `recall()` retorna vazio. Agente as vezes comenta *"vejo que voce ainda nao tem historico..."*.

**Causa:** Generator do bloco nao checa se `facts` esta vazio.

**Fix:** No wiring (secao 21.5), so emitir o bloco quando `facts` tiver pelo menos 1 entrada. `context_injection=None` quando vazio.

### Anti-pattern 5: Drift de duplicacao manual

**Sintoma:** Cliente colocou a instrucao "leia o bloco..." em 4 agentes via `custom_prompt_suffix`, esqueceu o 5o (Knowledge). Knowledge ignora bloco; outros 4 leem. Comportamento inconsistente.

**Causa:** Pre-v0.39.0 nao havia primitivo lib-side; cliente duplicava manualmente.

**Fix:** Migrar para `memory_context_block_tag="long_term_memory"` em `create_*_network` (doc 19). Uma flag, todos os agentes.

### Anti-pattern 6: Usar `pre_run_hook` so para prepend

**Sintoma:**
```python
async def hook(messages):
    return [{"role": "system", "content": memory_block}] + messages
network.pre_run_hook = hook
```

Hook abusado para fazer prepend; intent fica escondido atras de uma funcao.

**Fix:** Usar `context_injection=[{"role": "system", "content": memory_block}]` em `network.run(...)` ou `run_with_memory(...)` (doc 20). Hook fica disponivel para transformacoes reais (compactar memoria, filtrar PII).

## 21.5 — Wiring completo end-to-end

Padrao recomendado combinando as 3 primitivas + backend de memoria + dedup:

```python
from pathlib import Path
from typing import Any, Dict, List, Optional

from atendentepro import create_custom_network, run_with_history

# 1. Build network com memory_context_block_tag (doc 19) — todos os agentes
#    ja saberao consumir o bloco.
network = create_custom_network(
    templates_root=Path("./client_templates"),
    client="my_client",
    network_config={
        "triage": ["flow", "answer", "knowledge", "feedback"],
        "flow": ["interview", "answer"],
        "interview": ["answer"],
        "answer": ["triage"],
        "knowledge": ["triage"],
    },
    memory_context_block_tag="long_term_memory",  # doc 19
)


# 2. Helper que faz recall + format + dedup do backend de memoria.
async def build_memory_block(
    memory_service: Any,
    user_id: str,
    user_message: str,
    *,
    recall_limit: int = 3,
) -> Optional[str]:
    """Fan-out 3 metodos de recall, dedup por summary, cap recall_limit.

    Retorna o bloco XML pronto para injecao, ou None se nao ha facts.
    """
    # Fan-out: 3 vias diferentes para nao depender de uma so similaridade.
    # Exemplo com GRKMemory (adapte ao backend):
    semantic = await memory_service.recall(
        user_id=user_id, query=user_message, method="embedding", limit=recall_limit
    )
    graph = await memory_service.recall(
        user_id=user_id, query=user_message, method="graph", limit=recall_limit
    )
    recent = await memory_service.recall(
        user_id=user_id, query=user_message, method="recent", limit=recall_limit
    )

    # Dedup por summary (o mesmo fato pode vir das 3 vias).
    seen: set[str] = set()
    facts: List[str] = []
    for item in semantic + graph + recent:
        summary = (item.get("summary") or "").strip()
        if not summary or summary in seen:
            continue
        seen.add(summary)
        date_prefix = (item.get("date") or "").strip()
        facts.append(f"- {date_prefix}: {summary}" if date_prefix else f"- {summary}")
        if len(facts) >= recall_limit:
            break

    if not facts:
        return None  # NAO injetar bloco vazio (anti-pattern 4).

    return "<long_term_memory>\n" + "\n".join(facts) + "\n</long_term_memory>"


# 3. Per-request: gerar bloco e chamar network via context_injection (doc 20).
async def chat(user_id: str, user_message: str, history: List[Dict[str, Any]]):
    memory_block = await build_memory_block(
        memory_service=my_memory_service,
        user_id=user_id,
        user_message=user_message,
        recall_limit=3,
    )

    injection: Optional[List[Dict[str, Any]]] = (
        [{"role": "system", "content": memory_block}] if memory_block else None
    )

    result, new_history = await run_with_history(
        network,
        network.triage,
        [{"role": "user", "content": user_message}],
        history=history,
        user_id=user_id,
        context_injection=injection,  # doc 20
    )
    return result.final_output, new_history
```

Os 3 primitivos compoem ortogonalmente:

| Camada | Primitivo | Responsabilidade |
|---|---|---|
| Build-time (rede) | `memory_context_block_tag` (doc 19) | Instruir agentes a CONSUMIR o bloco |
| Recall (cliente) | `build_memory_block` helper | Fan-out + dedup do backend |
| Call-time (request) | `context_injection` (doc 20) | ADICIONAR o bloco ao payload |
| Triage prompt | Rule 0 hibrido (secao 21.2) | Rotear meta + hibrido sem handoff |

Apos isso, agentes downstream herdam a instrucao de leitura via doc 19 e nao precisam de prompt-engineering manual.

## 21.6 — Testes minimos recomendados

Para detectar regressoes do padrao em CI:

```python
# 1. Triage Rule 0 — meta puro
result, _ = await run_with_history(
    network, network.triage,
    [{"role": "user", "content": "o que ja conversamos?"}],
    context_injection=[{"role": "system", "content": "<long_term_memory>\n- 2026-04-12: Discutimos pricing.\n</long_term_memory>"}],
)
assert "pricing" in result.final_output.lower()

# 2. Triage Rule 0 — bloco ausente, topico hibrido
result, _ = await run_with_history(
    network, network.triage,
    [{"role": "user", "content": "sobre o fornecedor X que combinamos..."}],
)
assert "nao tenho registro" in result.final_output.lower() or "sem registro" in result.final_output.lower()
assert "nao houve" not in result.final_output.lower()  # anti-pattern 1

# 3. Anti-alucinacao numerica
result, _ = await run_with_history(
    network, network.answer,
    [{"role": "user", "content": "qual o orcamento Q1?"}],
    context_injection=[{"role": "system", "content": "<long_term_memory>\n- 2026-03-15: Budget Q1 era R$ 250k (estimativa).\n</long_term_memory>"}],
)
# Resposta NAO deve incluir "R$ 250k" literalmente sem tool_outputs validando.
# Pode mencionar "discutimos algo em torno disso, mas a fonte e os relatorios atuais"
# ou seguir para tool de consulta.
```

## 21.7 — Quando NAO usar long-term memory

- **Single-session bots** (atendimento curto, FAQ): adiciona complexidade sem retorno.
- **Domains regulados** sem clarificacao legal (LGPD/GDPR) sobre retencao de dados de usuario.
- **Compliance environments** (financeiro, saude) onde a memoria precisa de audit trail formal — usar storage de auditoria, nao memoria cross-session.

## 21.8 — Versionamento

- `memory_context_block_tag` (doc 19): v0.39.0+
- `context_injection` (doc 20): v0.40.0+
- Padrao canonico deste documento: aplicavel a partir de v0.40.0.
