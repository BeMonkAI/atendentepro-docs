# Passo 8 (opcional): janela de histórico (multi-turn)

> **Issue:** [#57 — context windowing / session summarization](https://github.com/BeMonkAI/atendentepro/issues/57)
> **Plano:** [docs/plans/2026-04-29-context-windowing.md](../plans/2026-04-29-context-windowing.md)

## Quando aplicar

Use este passo quando a aplicação:
- mantém uma sessão longa em que o usuário troca de assunto várias vezes;
- já apresentou degradação após o 2º/3º assunto (alucinações, troca de fluxo, latência alta);
- gera contas de inferência que crescem mais rápido do que o número de conversas.

Não aplicar em chatbots single-turn (1–2 perguntas por sessão) — o default
(`history_window = None`) preserva o comportamento original.

---

## API completa

```python
from atendentepro import HistoryWindow

HistoryWindow(
    max_messages=20,
    summarize_after_n_messages=10,
    summary_system_prompt="Resume os turnos abaixo em um paragrafo.",
    summary_model="gpt-4.1",
    on_agent_reset=lambda agent_name, msgs: None,
)
```

### Parâmetros e status de implementação

| Parâmetro | Tipo | Default | Status | Descrição |
|---|---|---|---|---|
| `max_messages` | `Optional[int]` | `None` | ✅ **ativo (Phase 4.1, v0.19.0)** | Trunca o histórico para os N itens mais recentes (mensagens `system` no topo são preservadas). `None` desativa truncamento. |
| `summarize_after_n_messages` | `Optional[int]` | `None` | ✅ **ativo (Phase 4.2, v0.20.0)** | Quando o histórico não-system passar de N, comprime os turnos antigos em uma única mensagem `system`. Requer um cliente OpenAI-compatível resolvível (via `get_async_client()` ou `network._summary_client`). |
| `summary_system_prompt` | `Optional[str]` | `None` | ✅ **ativo (Phase 4.2, v0.20.0)** | Override do prompt usado pelo LLM ao sumarizar. `None` cai num prompt PT-BR padrão (`DEFAULT_SUMMARY_PROMPT` em `_history.py`). |
| `summary_model` | `Optional[str]` | `None` | ✅ **ativo (Phase 4.2, v0.20.0)** | Modelo usado na sumarização. `None` usa `get_config().default_model`. |
| `on_agent_reset` | `Optional[Callable[[str, List[Dict]], None]]` | `None` | ✅ **ativo (Phase 4.3, v0.21.0)** | Callback disparado no início de cada turno quando o último agente que produziu output **NÃO** foi o Triage. Recebe `(agent_name, messages)` mutável — caller pode editar a lista in-place antes da sumarização/truncamento. Exceções são logadas (WARNING) e ignoradas. |

> **API congelada na v0.19.0**: clientes que declararam `summarize_after_n_messages` na v0.19.0 (quando era inativo) automaticamente ganham o comportamento na v0.20.0 — sem mudança de código.
>
> **Breaking change na v0.20.0**: `apply_history_window` virou `async`. Direct callers (que não usam `run_with_memory`) precisam adicionar `await`. `run_with_memory` foi atualizado internamente.

---

## Exemplo 1 — Truncamento simples (recomendado para começar)

```python
from pathlib import Path
from atendentepro import HistoryWindow, create_standard_network

network = create_standard_network(
    templates_root=Path("config"),
    client="meu_cliente",
)
network.history_window = HistoryWindow(max_messages=20)
```

Mantém apenas os 20 últimos itens user/assistant. Mensagens `system` no topo
(memória, instruções injetadas) sempre preservadas. Funciona via
`run_with_memory(network, ...)` automaticamente.

## Exemplo 2 — Truncamento + sumarização (Phase 4.2, ativo desde v0.20.0)

```python
network.history_window = HistoryWindow(
    max_messages=20,
    summarize_after_n_messages=10,
    summary_model="gpt-4.1",
)
```

A cada turno onde o histórico não-system tiver > 10 mensagens, a lib
faz uma chamada LLM extra (modelo configurável) para condensar os
turnos mais antigos em uma única mensagem `system` no topo, mantendo as
10 mais recentes verbatim. Truncamento (`max_messages`) atua depois,
como rede de segurança.

**Custos:**
- 1 chamada LLM extra por turno em que o threshold é cruzado.
- Latência: ~1–3s adicional (use o `default_model` da rede ou um modelo menor como `gpt-4.1-mini` para reduzir).
- Tokens: economia de 5–10x em conversas longas vs. forwarding sem janela.

**Fallback:** se a chamada de sumarização falhar (rede, quota, timeout),
a lib loga WARNING e cai para *drop-surplus* (mantém só as N kept) —
nunca trava o turno.

**Cliente OpenAI-compatível:** a lib resolve via
`atendentepro.utils.get_async_client()` por padrão. Para testes ou
clientes custom, atribua `network._summary_client = <client>` antes da
primeira chamada.

## Exemplo 3 — Configuração completa (Phase 4.3, ativo desde v0.21.0)

```python
def _on_subagent_finish(agent_name: str, msgs: list) -> None:
    if agent_name == "Knowledge Agent":
        # Limpa o último bloco de RAG para não poluir a próxima pergunta.
        del msgs[:-2]

network.history_window = HistoryWindow(
    max_messages=20,
    summarize_after_n_messages=10,
    summary_system_prompt=(
        "Voce resume turnos antigos de uma conversa de atendimento. "
        "Liste decisoes tomadas, fatos confirmados e pendencias em um "
        "unico paragrafo. Nao invente informacoes."
    ),
    summary_model="gpt-4.1",
    on_agent_reset=_on_subagent_finish,
)
```

---

## Reset callback (Phase 4.3, ativo desde v0.21.0)

Quando um sub-agente termina e o controle volta para o Triage, voce
pode injetar lógica custom (limpar memória de tool, marcar sessão,
trocar idioma) sem precisar wrappear `Runner.run`:

```python
def _on_subagent_finish(agent_name: str, msgs: list) -> None:
    if agent_name == "Knowledge Agent":
        # Limpa tudo exceto os 2 últimos turnos para não poluir
        # a próxima pergunta com o bloco de RAG anterior.
        del msgs[:-2]

network.history_window = HistoryWindow(
    max_messages=20,
    on_agent_reset=_on_subagent_finish,
)
```

**Como a lib detecta "controle voltou ao Triage":**
- `run_with_memory` salva `network.last_agent_name = result.last_agent.name` apos cada turno.
- No próximo turno, `apply_history_window` lê esse atributo. Se for diferente de `"Triage Agent"` (e não-None), dispara o callback.
- Para callers que NÃO usam `run_with_memory`: setar `network.last_agent_name` manualmente após `Runner.run`, ou aceitar que o callback nunca dispara.

**Garantias:**
- Callback recebe a lista MUTÁVEL — `msgs.clear()`, `del msgs[:N]`, ou substituição parcial são todas válidas.
- Roda ANTES de summarisation/truncamento — qualquer edição se propaga.
- Exceções são capturadas + logadas em WARNING — turno NÃO trava.
- `on_agent_reset = None` desativa sem warning.

## Quem chama Runner.run direto

A janela é aplicada automaticamente dentro de `run_with_memory`. Quem usa
`Runner.run(agent, messages)` direto precisa chamar o helper antes:

```python
from atendentepro import apply_history_window

windowed = apply_history_window(network, messages)
result = await Runner.run(network.triage, windowed)
```

> Desde a v0.20.0 (Phase 4.2), `apply_history_window` é `async` — direct
> callers precisam adicionar `await`. Quem usa `run_with_memory` não
> precisa mudar nada (a lib faz `await` internamente).

---

## Como funciona a truncação

| Mensagem | Conta para o limite? |
|---|---|
| `role="system"` no topo (instruções, memória injetada) | Não — sempre preservadas |
| `role="user"` / `role="assistant"` | Sim |

`max_messages=N` mantém apenas os N últimos itens user/assistant. Se há
3 system messages no topo + 50 turnos, e você define `max_messages=20`,
o resultado tem 3 system + 20 user/assistant = 23 mensagens.

### Casos de borda

- `max_messages = 0` derruba todo o histórico não-system (mantém só
  system messages no topo). Use só se quiser reset total entre cada turno.
- `max_messages = -1` (ou qualquer valor negativo) é tratado como `None`
  — emite WARNING no log, não trunca.
- Histórico com tamanho `≤ max_messages` retorna a lista original
  (mesma identidade — `is` returns True), evita cópia desnecessária.

---

## Cuidados

- Truncamento agressivo (≤ 5 mensagens) faz o agente esquecer contexto
  imediato. Comece com 20 e ajuste por bench.
- Mensagens `system` no topo (memória, instruções injetadas) NÃO contam
  para o limite e nunca são removidas.
- Em multi-tenant, defina `history_window` por rede após `create_standard_network`
  (cada tenant tem o próprio valor).

## Bench antes / depois

Antes de habilitar em produção, rode o bench multi-turn do cliente
(quando existir) com e sem `history_window`. A janela só faz sentido se
mover o pass rate ou cortar latência. Caso contrário, mantenha desligada.

## Exemplo executável

Veja [docs/examples/history_window/](../examples/history_window/) para um
exemplo end-to-end completo, com bench mínimo de simulação.

## Referências

- [Issue #57](https://github.com/BeMonkAI/atendentepro/issues/57) — context windowing / session summarization
- [docs/plans/2026-04-29-context-windowing.md](../plans/2026-04-29-context-windowing.md) — plan completo (truncamento + summarisation + reset callback)
- [atendentepro/_history.py](../../atendentepro/_history.py) — implementação (privada — público via `from atendentepro import HistoryWindow, apply_history_window`)
