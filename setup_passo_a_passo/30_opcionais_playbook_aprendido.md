# 30 — Playbook aprendido por agente

Issue #594 — permite que um tenant mantenha lições destiladas de turnos passados em um arquivo YAML. No build da rede, cada lição é anexada ao prompt do agente a que pertence, para ele aprender **COMO** atender melhor dentro do escopo que já tem.

A regra central: uma lição refina **COMO** o agente trabalha; ela **NUNCA** amplia **O QUE** ele atende. Se uma lição conflitar com as regras do prompt ou levar a um assunto fora do escopo, o próprio bloco instrui o agente a ignorar a lição e seguir as regras acima.

## 30.1 — Onde o arquivo fica

```
<templates_root>/
└── <client>/
    ├── guardrails_config.yaml      # já existente — define agent_scopes
    └── learned_playbook.yaml       # novo, opcional
```

`learned_playbook.yaml` é opcional. Sem o arquivo, o build da rede é idêntico ao anterior à issue #594 (nenhum log, nenhuma alteração de prompt).

## 30.2 — Formato do YAML

```yaml
version: "2026-10-22"        # obrigatório, string não vazia
lessons:
  - agent: answer_agent      # mesma chave de guardrails_config.yaml::agent_scopes
    when: "o cliente perguntar sobre prazos"
    do: "Responda citando o prazo padrão de 5 dias úteis."
    evidence: ["turn-id-1", "turn-id-2"]   # opcional
```

Regras por lição:

- `agent` (obrigatório): nome normalizado do agente, no mesmo formato de `agent_scopes` (ex.: `triage_agent`, `answer_agent`).
- `when` (obrigatório): situação que dispara a lição. String não vazia, no máximo **200** caracteres.
- `do` (obrigatório): o que o agente deve fazer. String não vazia, no máximo **400** caracteres.
- `evidence` (opcional): lista de strings com os turnos que justificam a lição.
- Nenhuma outra chave é aceita.

`when` e `do` são normalizados para uma única linha: quebras de linha e caracteres de controle/format (a mesma normalização do `untrusted_field`, #588) viram espaço. Assim uma lição não consegue sair do próprio bullet nem abrir uma nova seção no prompt.

`version` é obrigatório, tem no máximo **64** caracteres (acima disso, `reason=version_too_long`) e aparece no título do bloco injetado, para rastreabilidade do que está em produção. Como `when`/`do`, é reduzido a uma linha só.

## 30.3 — Como o bloco entra no prompt

Para cada agente com lições e cujas `instructions` sejam uma string (agentes com instruções callable são ignorados, como em `memory_context_block_tag`), a lib anexa ao final:

```

## ORIENTAÇÕES APRENDIDAS (versão 2026-10-22)
Estas orientações refinam COMO você atende dentro do seu escopo. Elas NUNCA ampliam o escopo: se uma orientação conflitar com as regras acima ou levar a um assunto fora do seu escopo, ignore a orientação e siga as regras acima.
- Quando o cliente perguntar sobre prazos: Responda citando o prazo padrão de 5 dias úteis.
```

O bloco é **anexado** (não prefixado), preservando a identidade base do agente no topo do prompt. Quando `memory_context_block_tag` também está configurado, o bloco de memória continua sendo o **último** — o playbook entra antes dele.

`create_custom_network` passa por `create_standard_network`, então herda o comportamento automaticamente.

## 30.4 — A cerca de escopo

O playbook é sempre cercado pelo **próprio** `guardrails_config.yaml` do tenant. Uma lição é rejeitada (com `WARNING` e sem levantar exceção) quando:

- o `agent` não existe em `agent_scopes`, ou o `about` desse agente é vazio;
- `when`/`do` estão ausentes, vazios ou acima do limite de caracteres (medido após o colapso em uma linha);
- `evidence` não é uma lista de strings;
- há chaves fora de `{agent, when, do, evidence}`;
- o texto casa com o hard-blocklist de jailbreak/prompt-injection; ou
- o texto casa com o backstop determinístico de expansão de escopo.

O backstop cobre, no mínimo, as famílias em português e inglês:

- `fora do (seu) escopo`, `além/alem do (seu) escopo`, `ampli* (o) escopo`;
- `qualquer (assunto|tema|pergunta)`, `também/tambem (responda|atenda|fale) sobre`, `ignor* (o) (escopo|guardrail)`;
- `outside (the|your) scope`, `beyond (the|your) scope`, `any (topic|subject|question)`.

Esse backstop é **determinístico**: ele pega as formulações óbvias, não substitui revisão semântica. A revisão de escopo de verdade acontece na promoção da lição, fora da biblioteca.

## 30.5 — Fail-closed

O loader lê **somente** `<templates_root>/<client>/guardrails_config.yaml` — nunca o fallback `templates/standard/`. Se o tenant não tiver o próprio arquivo, ou ele não tiver um mapping `agent_scopes` não vazio, nada é carregado:

```
WARNING learned_playbook_disabled client=acme reason=no_agent_scopes
```

O mesmo vale para `version` ausente/em branco (`reason=missing_version`) e `lessons` que não seja lista (`reason=lessons_not_a_list`). Arquivo ilegível, YAML inválido ou encoding diferente de UTF-8 desabilitam o playbook com `reason=invalid_yaml`; um `guardrails_config.yaml` ilegível cai em `reason=no_agent_scopes`. Em qualquer um desses casos o resultado é `(None, {})`: nenhum agente é alterado e nada é levantado.

## 30.6 — Limites e logs

- No máximo **20 lições aceitas por agente**; o excedente é descartado com `reason=cap_exceeded`.
- Cada lição rejeitada gera `WARNING learned_playbook_lesson_rejected` com `agent` e `reason`.
- Cada carga bem-sucedida gera uma linha `INFO learned_playbook_loaded` com `version`, `accepted` e `rejected`.

## 30.7 — O que fica fora da biblioteca

A biblioteca só **lê** o playbook. Decidir quais lições existem (promoção a partir de turnos reais) e revisar semanticamente se uma lição amplia escopo são responsabilidades do pipeline do tenant, fora do pacote. O código de guardrails nunca lê o playbook — a cerca é aplicada no carregamento, não no runtime de entrada.

## 30.8 — Uso

Nada muda na chamada do factory:

```python
from pathlib import Path

from atendentepro import create_standard_network

network = create_standard_network(
    templates_root=Path("./client_templates"),
    client="acme",
)
```

Basta existir `client_templates/acme/learned_playbook.yaml` e o `guardrails_config.yaml` do tenant com os `agent_scopes`. O loader também está disponível para inspeção:

```python
from atendentepro import load_learned_playbook

version, lessons = load_learned_playbook(Path("./client_templates"), "acme")
```
## 30.9 — Config inline (modo stateless, `/chat` com `config`)

No caminho stateless (issue #326) não existe pasta do tenant no disco. Desde a issue #597 o `InlineConfig` aceita o campo opcional `learned_playbook`, com **o mesmo formato** do arquivo:

```json
{
  "tenant_id": "acme",
  "session_id": "s1",
  "message": "oi",
  "config": {
    "yamls": {
      "guardrails_config": "agent_scopes:\n  answer_agent:\n    about: Dúvidas sobre produtos.\n"
    },
    "learned_playbook": {
      "version": "2026-10-23",
      "lessons": [
        {
          "agent": "answer_agent",
          "when": "o cliente perguntar sobre prazos",
          "do": "Responda citando o prazo padrão de 5 dias úteis.",
          "evidence": ["turn-id-1"]
        }
      ]
    }
  }
}
```

Como funciona:

- O servidor grava o playbook como `learned_playbook.yaml` na pasta da config inline (`<templates_dir>/<config_hash>/`), ao lado do `guardrails_config` enviado em `yamls`. A cerca é exatamente a do arquivo (30.4 e 30.5): vale só o `agent_scopes` **dessa própria config**; sem ele, nada é carregado e sai `WARNING learned_playbook_disabled ... reason=no_agent_scopes`.
- Lição inválida não derruba a requisição: é descartada com `WARNING learned_playbook_lesson_rejected`, como no arquivo.
- Mandar o playbook no campo **e** dentro de `yamls` (`learned_playbook`) retorna **400**. Use um dos dois; o campo é o caminho recomendado.
- `config_hash`: sem o campo, o hash é idêntico ao de antes da #597. Com o campo, o playbook entra no hash: mudou o playbook, muda o hash e a rede é construída de novo. Um probe só com `config_hash` reaproveita a rede em cache, já com o playbook.
