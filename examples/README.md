# AtendentePro — Usage Examples

Reference scripts that are **not imported** by the library. Each file is
a self-contained example you can copy into your own project and adapt.

Install requirements in **your** environment — AtendentePro itself
stays dependency-minimal.

## Prompt dialect adapter — `dialect/`

| File | What it shows |
|------|---------------|
| `dialect/compare.py` | Render one agent's canonical prompt in every dialect side-by-side and write the diffs to files. Useful when tuning transforms or debugging "why is Claude seeing `<section>` tags?". |
| `dialect/runtime_override.py` | Force a specific dialect for a single chat call (useful for A/B testing a dialect against the same model). |

## History windowing (multi-turn) — `history_window/`

| File | What it shows |
|------|---------------|
| `history_window/example_truncate.py` | `max_messages=N` cortando histórico antes do LLM (Phase 4.1). |
| `history_window/example_full_api.py` | Os 5 parâmetros de `HistoryWindow` ativos juntos: truncamento + sumarização + reset callback (Phase 4.1 + 4.2 + 4.3, v0.21.0). |
| `history_window/example_direct_runner.py` | Caller que usa `Runner.run` direto (sem `run_with_memory`) — precisa chamar `apply_history_window` manualmente. |

## Prompt optimization cache — `optim/`

| File | What it shows |
|------|---------------|
| `optim/dspy_external.py` | Minimum viable DSPy compile loop: one agent, one model, persist to cache. |
| `optim/dspy_bulk.py` | Compile **all 10** canonical prompts for a target model in a single pass (typical rollout workflow). |
| `optim/with_tester_metric.py` | Use monkai-tester's `ValidationEngine` as the DSPy metric (real evaluation against a client CSV instead of a dummy `lambda`). |

## Why these are not inside the package

AtendentePro does **not** bundle a prompt optimizer. Callers install
their own toolchain (DSPy, monkai-tester, or anything else) and use
`atendentepro.optim.store_optimized_prompt` to persist results. The
cache is a pure in/out store — AtendentePro reads at `_build_agent`
time and never imports the compiler.

This keeps the library's supply-chain surface minimal. See CHANGELOG
entry for v0.15.0 for rationale.

## Running

```bash
# From your OWN project (not inside the atendentepro venv):
pip install atendentepro dspy-ai  # or whatever your pipeline needs

# Copy an example and adapt paths/metrics.
python docs/examples/optim/dspy_external.py \
    --prompt-file my_prompt.txt \
    --model gpt-4.1-mini \
    --trainset my_data.jsonl
```
