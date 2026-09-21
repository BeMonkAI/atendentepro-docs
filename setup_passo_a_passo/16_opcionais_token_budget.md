# 16 — Per-tenant LLM token budget

`TokenBudgetLimiter` (issue #180) é uma camada **complementar** ao `RateLimiter` count-based existente. O `RateLimiter` conta requisições por janela; o `TokenBudgetLimiter` conta **tokens efetivamente consumidos** (input + output) por janela. Sem ele, um tenant em loop conversacional dentro do limite de requests pode queimar a chave LLM compartilhada com mensagens grandes.

Default: **desligado**. Sem configuração, comportamento é byte-a-byte idêntico ao da v0.29.x.

## 16.1 — Quando usar

- Você opera em modo serviço multi-tenant (FastAPI / `TenantManager`).
- Tenants compartilham a mesma chave LLM (cenário típico onde você cobra por uso).
- Algum tenant pode mandar mensagens grandes (RAG injetado, contexto longo) e estourar custo mesmo sob `RateLimiter`.

## 16.2 — Soft cap (importante)

A checagem do limite roda **antes** de `Runner.run`, mas o consumo só é conhecido **depois** da resposta. Por isso o limiter implementa um **soft cap**:

- A primeira requisição que estoura o teto **ainda passa** (não dá pra prever o custo antes da resposta).
- Requests seguintes dentro da janela são **bloqueadas** com `TokenBudgetExceededError` (HTTP 429 + `Retry-After` no service mode).

## 16.3 — Configuração via TenantManager

Em deploy com `TenantManager`:

```python
from atendentepro.service.manager import TenantManager

mgr = TenantManager(
    default_token_budget_max_tokens=100_000,    # 100k tokens por tenant
    default_token_budget_window_seconds=3600,   # janela de 1h
)
```

Cada tenant criado via `mgr.setup(...)` recebe o limiter próprio (estado isolado). Sem os parâmetros, `_TenantState.token_budget` fica `None` e o caminho de execução é o anterior.

## 16.4 — Configuração via env vars (service mode)

`atendentepro/service/app.py::create_app()` lê:

```bash
ATENDENTEPRO_TOKEN_BUDGET_MAX=100000          # opt-in: ausente ⇒ desligado
ATENDENTEPRO_TOKEN_BUDGET_WINDOW_SECONDS=3600 # default 1h
```

Quando `ATENDENTEPRO_TOKEN_BUDGET_MAX` está setado, todas as requests `/chat` passam pela checagem. Em caso de overage:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 1832
Content-Type: application/json

{"detail": "Token budget exceeded for 'tenant_a': 100123/100000 tokens used in the last 3600s. Retry in 1831.2s."}
```

## 16.5 — Uso direto (fora do TenantManager)

`TokenBudgetLimiter` é exportado no top-level e funciona com qualquer key opaca:

```python
from atendentepro import TokenBudgetLimiter, TokenBudgetExceededError

budget = TokenBudgetLimiter(max_tokens=10_000, window_seconds=60)

async def handle(user_id: str, message: str):
    try:
        budget.check(user_id)
    except TokenBudgetExceededError as exc:
        return f"Calma aí, retry em {exc.retry_after:.0f}s"
    result = await Runner.run(network.triage, message)
    budget.record(user_id, result.context_wrapper.usage.total_tokens)
    return result.final_output
```

## 16.6 — Limitação: ParallelNetwork

`ParallelNetwork.run()` retorna `str` puro (sem `RunResult`), portanto a integração no `TenantManager.chat` **não consegue extrair `usage.total_tokens`** para tenants em modo ensemble. Para esses tenants, o budget é checado mas não acumulado — comportamento equivale a "sem cap". Tracked como follow-up: `ParallelNetwork` precisa expor uma API alternativa que retorne usage agregado.

## 16.7 — Boas práticas

- Combine com `RateLimiter` (eles se complementam — request count e token count).
- Combine com `max_turns` (limita custo por run; sem ele, um único run pode estourar o teto sozinho).
- Defina o teto com base no plano comercial do tenant, não num número arbitrário.
- Janelas curtas (1-5 min) detectam abuso rápido; janelas longas (1h+) atuam como cota mensal/diária amortizada.
- A janela é deslizante por timestamp, então não há "reset à meia-noite" — entradas saem da janela conforme o tempo passa.
