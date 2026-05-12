# Setup passo a passo — AtendentePro

Esta pasta contém o guia de configuração da biblioteca AtendentePro em passos numerados. Você pode seguir manualmente ou **passar a pasta (ou o arquivo SETUP_COMPLETO_COPILOT.md) ao Copilot** e pedir que ele aplique as configurações no seu projeto.

## Índice

1. [01_instalacao.md](01_instalacao.md) — Pip install e extras opcionais
2. [02_variaveis_ambiente.md](02_variaveis_ambiente.md) — .env e variáveis obrigatórias/opcionais
3. [03_ativacao_e_primeira_rede.md](03_ativacao_e_primeira_rede.md) — activate(), create_standard_network(), primeiro run
4. [04_templates_obrigatorios.md](04_templates_obrigatorios.md) — Estrutura de pastas e triage_config.yaml mínimo
5. [05_opcionais_memoria.md](05_opcionais_memoria.md) — Memória GRK, user_id/session_id (resumo)
6. [06_opcionais_user_loader.md](06_opcionais_user_loader.md) — user_loader e session_id_factory (resumo)
7. [07_cuidados_principais.md](07_cuidados_principais.md) — Principais cuidados (segurança, isolamento, boas práticas)
8. [08_opcionais_history_window.md](08_opcionais_history_window.md) — Janela de histórico (truncamento + sumarização) para sessões longas (issue #57)
9. [09_opcionais_run_with_history.md](09_opcionais_run_with_history.md) — `run_with_history` para preservar tool outputs em multi-turn (issue #119)
10. [10_opcionais_guardrails_preflight.md](10_opcionais_guardrails_preflight.md) — `run_input_guardrails` para preflight standalone com history role-tagged (issue #122)
11. [11_opcionais_sticky_agent.md](11_opcionais_sticky_agent.md) — `sticky_agent_hint` para reduzir re-roteamento espúrio do Triage (issue #120)
12. [12_opcionais_multiagent_hierarquia.md](12_opcionais_multiagent_hierarquia.md) — Multi-agent hierarchy (manager + specialists, v0.26.0)
13. [13_opcionais_multiagent_ensemble.md](13_opcionais_multiagent_ensemble.md) — Multi-agent ensemble (`ParallelNetwork`, v0.26.0)
14. [14_factory_canonico.md](14_factory_canonico.md) — `set_agent_instructions` + `create_custom_network(**kwargs)` (issues #198 #199, v0.30.0)
15. [15_opcionais_pre_run_hook.md](15_opcionais_pre_run_hook.md) — `pre_run_hook` + `end_session` + `memory_backend` typed field (issues #195 #196 #197, v0.30.0)
16. [16_opcionais_token_budget.md](16_opcionais_token_budget.md) — `TokenBudgetLimiter` per-tenant LLM token budget (issue #180, v0.30.0)
17. [SETUP_COMPLETO_COPILOT.md](SETUP_COMPLETO_COPILOT.md) — Fluxo único para colar no Copilot (todos os passos + cuidados)

## Referências

- [README principal do repositório](../../README.md) — Instalação, ativação, API Key, início rápido, arquitetura
- [atendentepro/memory/README.md](../../atendentepro/memory/README.md) — Memória de contexto longo, user_id/session_id, canal compartilhado
- [docs/examples/](../examples/) — Exemplos executáveis (memory_user_session, user_loader, agent_style, etc.)
