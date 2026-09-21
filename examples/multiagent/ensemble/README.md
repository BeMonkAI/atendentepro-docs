# Exemplo: ensemble multi-agente (3 personas + coordenador)

Demonstra a API publica introduzida pelos issues #150 / #151:
`ParallelNetwork`, `BaseNetwork` (Protocol) e `signal_subclass`.
**Ativos desde a v0.25.0**.

Ver [passo 13 do setup](../../../setup_passo_a_passo/13_opcionais_multiagent_ensemble.md)
e [plano completo](../../../plans/2026-05-06-multi-agent.md).

## Arquivos

| Arquivo | O que mostra |
|---|---|
| `multiagent_config.yaml` | YAML com `network_type: parallel`, 3 personas (`persona_value`, `persona_growth`, `persona_macro`) + coordenador (`portfolio_manager`), tunaveis (`parallel_timeout_s`, `parallel_max_concurrency`, `parallel_partial_ok`). |
| `client_resources/signals.py` | Define `PersonaSignal = signal_subclass("PersonaSignal", {"recommendation": (str, ""), "horizon_months": (int, 12)})`. Toda persona do fanout precisa declarar um `output_schema` e este e o que o YAML aponta. |
| `run.py` | Script Python end-to-end. Constroi um `ParallelNetwork` direto (sem ir pela fabrica), monkeypatcha `_runner_run` para devolver `PersonaSignal` canned por persona + string canned no coordenador, roda `network.run(messages)` e imprime o resultado. |

## Como rodar

A partir desta pasta:

```bash
cd docs/examples/multiagent/ensemble
PYTHONPATH=../../../.. python run.py
```

O exemplo NAO faz chamadas LLM reais — ele monkeypatcha
`atendentepro.multiagent.invoke._runner_run` (a mesma tecnica usada por
`tests/multiagent/conftest.py`) para devolver `PersonaSignal` instances
por persona e uma string final do coordenador. Nao precisa de
`OPENAI_API_KEY` nem licenca para rodar.

## Saida esperada

```
--- Demo: ParallelNetwork (3 personas + coordinator) ---
  fanout: ['persona_value', 'persona_growth', 'persona_macro']
  coordinator: portfolio_manager
  final answer: Portfolio Manager: 2/3 personas recommend BUY (value & macro), 1/3 HOLD (growth). Net call: BUY with a 18-month horizon.

OK — multi-agent ensemble demo finished.
```

## Como adaptar para um cliente real

1. Copie `multiagent_config.yaml` para
   `client_templates/<seu_cliente>/multiagent_config.yaml`.
2. Mantenha `client_resources/signals.py` (ou crie a sua propria
   subclasse de `AgentSignal`); o `output_schema` precisa estar sob o
   prefixo `client_resources.` por padrao — veja a allowlist no passo 13.
3. Construa a rede via fabrica em vez de instanciar `ParallelNetwork`
   manualmente:
   ```python
   from atendentepro import activate, configure, create_parallel_network

   activate("...")
   configure(provider="openai", openai_api_key="...")
   network = create_parallel_network(
       templates_root=Path("client_templates"),
       client="seu_cliente",
   )
   final = await network.run([{"role": "user", "content": "..."}])
   ```
4. Remova o monkeypatch de `_runner_run` — em producao o SDK chama os
   agentes reais.

## Quando usar ensemble em vez do pipeline padrao

| Cenario | Recomendacao |
|---|---|
| Atendimento sequencial (Triage → Flow → Answer) | **Nao use ensemble** — o default e mais barato e simples. |
| 1 manager LLM decide qual especialista chamar em runtime | Use **hierarquia** (passo 12). |
| N personas opinam **EM PARALELO** sobre o mesmo input e um coordenador sintetiza | Use **ensemble** (passo 13, este exemplo). |
| Falha de uma persona deve abortar | `parallel_partial_ok: false` (default). |
| Falha de uma persona pode ser ignorada (dashboard, sumario) | `parallel_partial_ok: true`. |
