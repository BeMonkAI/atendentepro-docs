# 23 — Memória de longo prazo declarativa por tenant

Issue [#319](https://github.com/BeMonkAI/atendentepro/issues/319) — a partir da v0.49.0, qualquer tenant servido pelo `create_app()` multi-tenant pode ligar memória de longo prazo (GRKMemory) **só por configuração** no payload do `POST /setup`, sem precisar escrever código de wiring, `pre_run_hook` ou `context_injection` manual.

Leia este documento em conjunto com os outros dois documentos do subsistema de memória:

- **Doc 19 — `memory_context_block_tag`**: instrui TODOS os agentes a CONSUMIR o bloco `<tag>…</tag>`.
- **Doc 21 — Padrão canônico end-to-end**: prompts recomendados (Rule 0 Triage), anti-patterns capturados em prod e wiring completo para quem ainda usa a API de baixo nível.

---

## 23.1 — O que mudou

**Antes (#319):** para ligar memória em um tenant multi-tenant, o operador precisava registrar um `pre_run_hook` no servidor (código Python), chamar `memory_service.recall(...)` manualmente, formatar o bloco XML, injetá-lo via `context_injection` em cada `/chat` e, separadamente, chamar `memory_service.save(...)` ao final — tudo fora da lib.

**Depois (#319):** enviar `"memory": {"enabled": true, ...}` no payload do `POST /setup`. A lib constrói o backend GRKMemory, o acopla ao tenant e toda chamada `/chat` desse tenant passa automaticamente pelo pipeline:

```
/chat → search (recall) → inject (prepend bloco XML) → run (rede de agentes) → save (persiste o turno)
```

Nenhum código adicional no servidor ou no cliente é necessário.

---

## 23.2 — Pré-requisitos

1. **Dependência de memória instalada:**
   ```bash
   pip install "atendentepro[memory]"
   ```

2. **Variável de ambiente `GRKMEMORY_API_KEY`** configurada no servidor (Railway, Azure, Docker etc.). A lib lê a chave ao processar o `/setup` — se a variável estiver ausente, o endpoint rejeita o payload com erro descritivo.

3. **`user_context.user_id` obrigatório em todo `POST /chat`** quando memória está ativa. A memória usa `user_id` para isolar conversas entre usuários diferentes. Se `user_id` não for enviado, o `/chat` falhará de forma explícita (não silenciosa).

4. **`memory_context_block_tag` recomendado.** Sem ele, o bloco XML é injetado mas os agentes não recebem instrução para lê-lo — comportamento inconsistente. Veja o [doc 19](19_opcionais_memory_context_block_tag.md) para entender por que a tag é necessária.

---

## 23.3 — Como ligar: payload do `POST /setup`

```json
POST /setup
{
  "tenant_id": "acme",
  "yamls": {
    "triage_config": "...",
    "flow_config": "..."
  },
  "memory_context_block_tag": "long_term_memory",
  "memory": {
    "enabled": true,
    "backend": "grk",
    "search_method": "graph",
    "memory_limit": 5,
    "memory_threshold": 0.3,
    "memory_header": null
  }
}
```

### Campos do bloco `memory` (`MemorySetup`)

| Campo | Tipo | Default | Descrição |
|---|---|---|---|
| `enabled` | `bool` | `false` | Quando `true`, `/chat` é roteado pelo pipeline de memória (search → inject → save). |
| `backend` | `"grk"` | `"grk"` | Backend de memória. Único valor aceito hoje. |
| `search_method` | `str` | `"graph"` | Método de recall do GRKMemory: `"graph"`, `"embedding"`, `"recent"`, etc. |
| `memory_limit` | `int` | `5` | Máximo de memórias injetadas por turno (1–50). |
| `memory_threshold` | `float` | `0.3` | Limiar mínimo de similaridade para o recall (0.0–1.0). |
| `memory_header` | `str \| null` | `null` | Cabeçalho pré-pendo ao bloco de memória injetado. `null` usa o default da lib. |

> **Nota sobre `backend`:** o único valor aceito é `"grk"`. O campo existe para extensibilidade futura. Enviar qualquer outro valor retorna erro de validação do Pydantic.

### Equivalente via Python (TenantManager direto)

A interface canônica é o corpo JSON do `/setup` acima. Ao chamar
`TenantManager.setup()` diretamente, o parâmetro `memory` é um **dict**
(`Optional[Dict[str, Any]]`) — o mesmo shape do bloco `memory` do JSON.
Passar um objeto `MemorySetup` diretamente **falha** (`setup()` chama
`.get()` no dict). Use um dict literal ou `MemorySetup(...).model_dump()`:

```python
await mgr.setup(
    tenant_id="acme",
    yamls={...},
    memory_context_block_tag="long_term_memory",
    memory={
        "enabled": True,
        "backend": "grk",
        "search_method": "graph",
        "memory_limit": 5,
        "memory_threshold": 0.3,
    },
)

# Ou, reaproveitando o modelo Pydantic para validação:
from atendentepro.service.schemas import MemorySetup

await mgr.setup(
    tenant_id="acme",
    yamls={...},
    memory_context_block_tag="long_term_memory",
    memory=MemorySetup(
        enabled=True,
        backend="grk",
        search_method="graph",
        memory_limit=5,
        memory_threshold=0.3,
    ).model_dump(),
)
```

---

## 23.4 — O que acontece em cada `/chat`

Quando `memory.enabled=true` está configurado para o tenant, cada requisição `/chat` percorre este pipeline automaticamente:

1. **Search (recall):** a lib chama o backend GRKMemory com a última mensagem do usuário e o `user_id` como chave de isolamento. Retorna até `memory_limit` memórias com similaridade ≥ `memory_threshold`.

2. **Inject:** as memórias recuperadas são formatadas em um bloco XML:
   ```
   <long_term_memory>
   - 2026-04-12: Usuário preferiu relatórios em PDF.
   - 2026-05-03: Decisão sobre fornecedor Y adiada para Q3.
   </long_term_memory>
   ```
   O bloco é pré-pendido ao payload como mensagem `system` antes de invocar a rede de agentes. Se `memory_header` estiver configurado, ele é adicionado antes do conteúdo.

3. **Run:** a rede de agentes executa normalmente. Os agentes recebem o bloco via contexto (enriquecido pelo `memory_context_block_tag` se configurado — veja o [doc 19](19_opcionais_memory_context_block_tag.md)).

4. **Save:** após a execução, a lib persiste o turno (mensagem do usuário + resposta do agente) no backend GRKMemory, usando `user_id` + `session_id` como chaves de identificação.

Se o recall retornar vazio, o bloco **não é injetado** (anti-pattern 4 do [doc 21](21_long_term_memory_canonical_pattern.md): bloco vazio confunde agentes).

---

## 23.5 — Exemplo completo: `/chat` com memória ativa

```json
POST /chat
{
  "tenant_id": "acme",
  "session_id": "sess_abc123",
  "message": "Qual o status do fornecedor Y?",
  "user_context": {
    "user_id": "usr_42"
  }
}
```

Resposta esperada (memória enriquece o contexto silenciosamente):

```json
{
  "response": "Conforme discutido anteriormente, a decisão sobre o fornecedor Y foi adiada para Q3. Gostaria de agendar uma revisão ou precisa de alguma outra informação?",
  "agent_name": "answer"
}
```

> **Atenção:** se `user_context.user_id` for omitido e o tenant tiver memória ativa, o `/chat` retorna HTTP 400 com mensagem de erro explicativa.

---

## 23.6 — Configuração mínima vs. configuração completa

**Mínima (defaults adequados para a maioria dos casos):**

```json
"memory": {
  "enabled": true
}
```

**Completa (controle fino):**

```json
"memory_context_block_tag": "long_term_memory",
"memory": {
  "enabled": true,
  "backend": "grk",
  "search_method": "embedding",
  "memory_limit": 3,
  "memory_threshold": 0.5,
  "memory_header": "## Contexto de sessões anteriores"
}
```

---

## 23.7 — Comparação com o padrão canônico (doc 21)

O [doc 21](21_long_term_memory_canonical_pattern.md) descreve o padrão de wiring manual (fan-out de 3 métodos de recall, dedup por summary, `context_injection` explícito por request). Esse padrão continua válido e oferece mais controle:

| Aspecto | Declarativo (#319, este doc) | Manual (doc 21) |
|---|---|---|
| Configuração | JSON no `/setup` | Código Python no servidor |
| Recall | Método único (`search_method`) | Fan-out de até 3 métodos + dedup |
| Dedup | Gerenciado pela lib | Gerenciado pelo cliente |
| Injeção | Automática por turno | `context_injection` explícito |
| Save | Automático | Chamada manual ao backend |
| Controle | Menor (suficiente para maioria) | Total |

**Recomendação:** começar com o modo declarativo. Migrar para o wiring manual do doc 21 somente se o comportamento do recall precisar de customização fina (ex: fan-out multi-método, dedup por campo customizado, salvar metadados adicionais).

---

## 23.8 — Anti-patterns específicos do modo declarativo

### `user_id` ausente no `/chat`

```json
// Errado — user_context sem user_id
"user_context": { "role": "admin" }

// Certo — user_id sempre presente quando memória está ativa
"user_context": { "user_id": "usr_42", "role": "admin" }
```

### `memory_context_block_tag` ausente

Ligar `memory.enabled=true` sem `memory_context_block_tag` faz o bloco ser injetado mas os agentes não recebem instrução para consumi-lo — comportamento silenciosamente inconsistente. Sempre setar os dois juntos.

### Threshold muito alto

`memory_threshold=0.9` em produção resulta em recall vazio na maioria dos turnos. Começar com `0.3` (default) e ajustar após análise de logs.

### `backend` diferente de `"grk"`

O campo só aceita `"grk"`. Enviar outro valor retorna erro 422 imediatamente — não é falha silenciosa.

---

## 23.9 — Versionamento

Disponível a partir da v0.49.0.

Primitivos anteriores que compõem este pipeline:

- `memory_context_block_tag` (doc 19): v0.39.0+
- `context_injection` (doc 20): v0.40.0+
- Padrão canônico manual (doc 21): v0.40.0+
- Declarativo por tenant este doc (doc 23): v0.49.0+
