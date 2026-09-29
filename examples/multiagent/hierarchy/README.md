# Exemplo: hierarquia multi-agente (manager + 2 especialistas)

Demonstra a API publica introduzida pelos issues #147 / #148 / #149:
`AgentMetadata`, `MultiAgentState`, `invoke_agent` e
`build_call_agent_tool`. **Ativos desde a v0.25.0**.

Ver [passo 12 do setup](../../../setup_passo_a_passo/12_opcionais_multiagent_hierarquia.md)
e [plano completo](../../../plans/2026-05-06-multi-agent.md).

## Arquivos

| Arquivo | O que mostra |
|---|---|
| `multiagent_config.yaml` | YAML de configuração do produto: manager + valuation_specialist + risk_specialist com `can_call`, `exposed_to_user`, `output_schema`, `builtin_tools: [call_agent]`. |
| `run.py` | Script Python end-to-end. Mostra três caminhos: (A) `invoke_agent` direto, (B) `build_call_agent_tool` invocado como o SDK faria, (C) `CallAgentForbidden` quando o caller tenta sair da whitelist. |

## Como rodar

A partir da raiz do repo:

```bash
python -m docs.examples.multiagent.hierarchy.run
```

O exemplo NÃO faz chamadas LLM reais — ele monkeypatcha
`atendentepro.multiagent.invoke._runner_run` (a mesma técnica usada por
`tests/multiagent/conftest.py`) para devolver `RiskSignal` /
`ValuationSignal` canned. Não precisa de `OPENAI_API_KEY` nem licença
para rodar.

## Saída esperada

```
--- Demo A: invoke_agent direct (no LLM in the loop) ---
  state.agent_calls keys: ['valuation_specialist']
  invoke result: verdict='approve' fair_price=42.5 reasoning='P/E within target band.'

--- Demo B: build_call_agent_tool (whitelist enforced) ---
  manager received: {"text": "verdict='approve' risk_score=22 reasoning='...'"}

--- Demo C: CallAgentForbidden when target is off-whitelist ---
  caught CallAgentForbidden: Agent 'manager' is not allowed to call 'risk_specialist'. Allowed targets (can_call): ['valuation_specialist'].

OK — multi-agent hierarchy demo finished.
```

## Como adaptar para um cliente real

1. Mova `multiagent_config.yaml` para
   `client_templates/<seu_cliente>/multiagent_config.yaml`.
2. Crie `client_resources/signals.py` com as classes
   `ValuationSignal` / `RiskSignal` (o `output_schema` precisa estar sob
   o prefixo `client_resources.` por padrão — veja a allowlist no passo
   12).
3. Adicione os agentes `manager`, `valuation_specialist`,
   `risk_specialist` à `AgentNetwork` (`create_custom_network` ou
   `create_standard_network`). A factory lê o YAML, popula
   `network.agent_metadata` e anexa o `call_agent` tool ao manager
   automaticamente.
4. Remova o monkeypatch de `_runner_run` — em produção o SDK chama os
   agentes reais.

## Quando usar a hierarquia em vez do pipeline padrão

| Cenário | Recomendação |
|---|---|
| Atendimento sequencial (Triage → Flow → Answer) | **Não use hierarquia** — o default é mais barato e simples. |
| Roteamento por domínio com especialistas isolados | Manager + especialistas com `exposed_to_user: false`. |
| Especialista deve entregar payload estruturado para o caller | `output_schema: client_resources.signals.X` no especialista. |
| LLM-driven decision (manager decide qual especialista chama em runtime) | `builtin_tools: [call_agent]` no manager. |
