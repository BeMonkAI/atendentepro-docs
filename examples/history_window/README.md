# 🪟 Exemplo: Janela de histórico (multi-turn)

Demonstra os 5 parâmetros de `HistoryWindow` para conversas longas
multi-turn. **Os 5 parâmetros estão ATIVOS desde a v0.21.0**
(Phase 4.3).

Ver [issue #57](https://github.com/BeMonkAI/atendentepro/issues/57) e
[plan completo](../../plans/2026-04-29-context-windowing.md).

## Arquivos

| Arquivo | O que mostra |
|---|---|
| `example_truncate.py` | Apenas `max_messages` (Phase 4.1) |
| `example_full_api.py` | API completa com todos os 5 params ativos (Phase 4.1 + 4.2 + 4.3) |
| `example_direct_runner.py` | Quem chama `Runner.run` direto (sem `run_with_memory`) |

## Como rodar

```bash
# A partir da raiz do repo:
python -m docs.examples.history_window.example_truncate
python -m docs.examples.history_window.example_full_api
python -m docs.examples.history_window.example_direct_runner
```

Os exemplos não fazem chamada LLM real — usam um stub de `Runner.run`
para que possam ser executados em CI sem credenciais.

## Quando usar cada knob

| Sintoma | Knob recomendado |
|---|---|
| Latência > 30s em conversas com 5+ turnos | `max_messages=20` (Phase 4.1) |
| Cliente perde contexto crítico de 30 turnos atrás | + `summarize_after_n_messages=10` (Phase 4.2) |
| Routing degrada quando Triage retoma controle pós sub-agente | + `on_agent_reset=...` (Phase 4.3) |
