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
8. [SETUP_COMPLETO_COPILOT.md](SETUP_COMPLETO_COPILOT.md) — Fluxo único para colar no Copilot (todos os passos + cuidados)

## Referências

- [README principal do repositório](../../README.md) — Instalação, ativação, API Key, início rápido, arquitetura
- [atendentepro/memory/README.md](../../atendentepro/memory/README.md) — Memória de contexto longo, user_id/session_id, canal compartilhado
- [docs/examples/](../examples/) — Exemplos executáveis (memory_user_session, user_loader, agent_style, etc.)
