# Principais cuidados

Este documento lista os **principais cuidados** que o usuário (e o Copilot) devem tomar ao configurar e operar o AtendentePro.

## Credenciais e .env

- **Nunca commitar** o arquivo `.env` nem chaves reais. Incluir `.env` no `.gitignore`.
- **Não colar** tokens ou API keys em código; usar sempre variáveis de ambiente ou arquivo `.env`.

## Ativação e ordem de uso

- Chamar **`activate()`** antes de qualquer uso da rede (`create_standard_network`, `Runner.run`, `run_with_memory`). Sem ativação, a biblioteca não funciona.

## Isolamento multi-usuário e memória

- Em ambiente com **mais de um usuário** ou **canal compartilhado** (um WhatsApp, e-mail ou Teams para vários clientes), **sempre** informar `user_id` em cada chamada a `run_with_memory` (ou garantir que o user_loader retorne o user_id do **request atual**). Caso contrário, memórias podem ser compartilhadas entre usuários.
- Em canal compartilhado: **session_id** = identificador do canal; **user_id** = identificador do cliente naquela conversa (ex.: número do contato, e-mail do remetente).
- Se derivar `session_id` por hash (ex.: últimas mensagens), **incluir user_id no hash** para evitar colisão entre usuários.

## user_loader

- O user_loader deve retornar dados do **usuário/request atual** (ex.: extrair do JWT ou do canal). Não reutilizar contexto de outro request; senão memória e filtros podem ser aplicados ao usuário errado.
- Usar user_loader apenas para **dados do usuário** (perfil, role, metadata). Não usar para memória nem para session_id; session_id deve vir de parâmetro ou `network.session_id_factory`.

## Segurança (prompt injection e extensões)

- **Não concatenar** input do usuário em system prompts. A biblioteca já mitiga RAG e guardrail (ver [docs/SECURITY.md](../SECURITY.md)); ao criar novas tools ou prompts que usem texto do usuário, delimitar claramente dados vs instruções e reforçar o system prompt contra seguimento de instruções no conteúdo do usuário.
- Em cenários sensíveis, **preferir** identificar o usuário por canal autenticado (token, sessão) em vez de depender só de texto livre da conversa.

## Guardrail de escopo: cuidado em multi-turn

- O **scope validator nativo** da biblioteca (LLM) já trata follow-ups curtos (`"sim"`, `"ok"`, `"1"`, `"esse"`, nome de marca isolado, etc.) como dentro do escopo, porque raciocina semanticamente sobre o turno atual.
- **Se você substituir o scope validator por um heurístico próprio** (keyword/regex, por custo ou latência), você **NÃO herda esse comportamento**: respostas curtas a perguntas do agente podem ser classificadas como fora de escopo e bloqueadas (~500ms de latência desperdiçada + UX quebrada).
- **Mitigação recomendada para heurísticos customizados**: detectar se a última mensagem do assistant terminou com `"?"` e, em caso afirmativo, aceitar respostas curtas ou itens de uma allowlist configurável (`sim/não/ok/1/2/esse/abre/cancela/...`). Implementação de referência: PRs [#87](https://github.com/BeMonkAI/marketing_insights_nestle_engine/pull/87) e [#91](https://github.com/BeMonkAI/marketing_insights_nestle_engine/pull/91) do `marketing_insights_nestle_engine`. Acompanhar a issue [#122](https://github.com/BeMonkAI/atendentepro/issues/122) para a expansão futura da API (`run_input_guardrails(..., history=...)`).

## Templates e caminhos

- A pasta de templates deve **existir** e conter pelo menos **`triage_config.yaml`**. O par `templates_root` + `client` deve apontar para essa pasta (ex.: `templates_root=Path("config")`, `client="meu_cliente"` implica que exista `config/meu_cliente/triage_config.yaml`).

## Nota para o Copilot

Ao aplicar o setup, respeitar estes cuidados; em especial: não commitar .env, ativar antes de usar a rede, e em multi-usuário ou canal compartilhado sempre passar user_id (e session_id quando aplicável).

## Referências

- [docs/SECURITY.md](../SECURITY.md) — Superfícies de risco e mitigações
- [docs/examples/memory_user_session/README.md](../examples/memory_user_session/README.md) — Seção "Evitar confusão entre usuários"
