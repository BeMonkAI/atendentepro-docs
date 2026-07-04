# 14 — Padrões canônicos de factory: `set_agent_instructions` + `create_custom_network(**kwargs)`

Estes dois padrões resolvem dois pés-de-coelho recorrentes ao customizar a rede após a construção (issues #198 e #199).

## 14.1 — `set_agent_instructions` é o jeito canônico de mutar instruções pós-build

Cada agente é montado pelo factory com um **bloco de estilo** (`## Estilo de Comunicação`) anexado ao final das instruções, mais o adapter de dialect do provider configurado. Quando você sobrescreve `agent.instructions = "..."` direto, esse bloco é destruído silenciosamente — o agente passa a responder sem o tom/estilo configurado e sem o prefixo recomendado pelo SDK.

A função `set_agent_instructions(agent, instructions)` é o caminho oficial: ela preserva o style block existente e re-aplica o adapter de dialect.

```python
from atendentepro import (
    activate,
    create_standard_network,
    set_agent_instructions,
)

activate("...")
network = create_standard_network(templates_root=..., client="acme")

# CORRETO — preserva style + dialect
set_agent_instructions(
    network.knowledge,
    "Você é o agente de Conhecimento. Responda apenas com base nos documentos fornecidos.",
)

# ERRADO — descarta o style block, perde o adapter de dialect
network.knowledge.instructions = "Você é o agente de Conhecimento. ..."
```

Quando usar:

- Você precisa injetar trechos calculados em runtime (ex: prompt template renderizado com dados do tenant).
- Você precisa concatenar uma seção custom às instruções base.
- Você está em um teste e quer trocar o prompt sem reconstruir a rede inteira.

Quando NÃO usar:

- Configuração estática por cliente — prefira `triage_custom_instructions` (e equivalentes) no factory ou os YAMLs de prompt em `client_templates/<cliente>/`.

## 14.2 — `create_custom_network` aceita `**kwargs` (v0.30.0)

Antes da v0.30.0, `create_custom_network` só repassava `templates_root`, `client`, `include_onboarding` e `custom_tools`. Quem usava custom-network e queria `user_loader`, `agent_providers`, `agent_models`, `conditional_prompts`, `global_style`, etc., tinha que setar atributo a atributo depois (`network.user_loader = ...`), perdendo type hints e correndo o risco de esquecer um campo.

A partir da v0.30.0, qualquer keyword-arg suportado por `create_standard_network` é aceito e repassado verbatim:

```python
from atendentepro import create_custom_network

network = create_custom_network(
    templates_root=Path("./client_templates"),
    client="acme",
    network_config={
        "triage": ["flow", "feedback"],
        "flow": ["interview", "triage"],
    },
    # Tudo abaixo é forwarded para create_standard_network:
    user_loader=my_user_loader,
    agent_providers={"knowledge": ProviderConfig(provider="deepseek", model="deepseek-reasoner")},
    agent_models={"triage": "gpt-4.1-mini"},
    conditional_prompts={...},
    global_style=AgentStyle(tone="profissional", language_style="formal"),
)
```

Restrições:

- **Não passe** `templates_root`, `client`, `custom_tools` ou `include_onboarding` via `**kwargs` — esses já são argumentos posicionais/explícitos e Python levanta `TypeError` se duplicados.
- `include_onboarding` é derivado automaticamente de `network_config` (`"onboarding" in network_config`); para fluxos com onboarding, basta listar os handoffs do agente onboarding em `network_config`.
