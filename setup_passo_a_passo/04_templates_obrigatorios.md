# Passo 4: Templates obrigatórios

## Objetivo

Criar a estrutura mínima de pastas e o arquivo `triage_config.yaml` obrigatório para a rede funcionar.

## Estrutura mínima

Uma pasta com o nome do cliente (ex.: `meu_cliente`) deve existir dentro de `templates_root`. Essa pasta deve conter **pelo menos** o arquivo `triage_config.yaml`.

Exemplo de estrutura:

```
config/
└── meu_cliente/
    └── triage_config.yaml
```

Se `templates_root=Path("config")` e `client="meu_cliente"`, o caminho efetivo é `config/meu_cliente/triage_config.yaml`.

## Conteúdo mínimo de triage_config.yaml

O arquivo define palavras-chave por agente e regras de roteamento. Abaixo um exemplo mínimo; você pode expandir depois com mais keywords e agentes.

Crie o arquivo `triage_config.yaml` dentro da pasta do cliente com o conteúdo:

```yaml
agent_keywords:
  flow_agent:
    keywords: ["fluxo", "processo", "opções", "menu"]
    description: "Fluxos e opções"
  knowledge_agent:
    keywords: ["conhecimento", "documentação", "dúvida", "informação"]
    description: "Base de conhecimento"
  answer_agent:
    keywords: ["resposta", "ajuda", "suporte"]
    description: "Respostas diretas"

routing_rules:
  priority_order:
    - "answer_agent"
    - "knowledge_agent"
    - "flow_agent"
  default_agent: "knowledge_agent"
```

## Outros arquivos YAML (opcionais)

Podem ser adicionados depois, conforme necessidade. Se não existirem, a biblioteca usa valores padrão.

| Arquivo | Descrição |
|---------|-----------|
| `flow_config.yaml` | Menu e tópicos |
| `interview_config.yaml` | Perguntas para coleta de dados |
| `answer_config.yaml` | Template de resposta final |
| `knowledge_config.yaml` | RAG e base de conhecimento |
| `escalation_config.yaml` | Transferência para humano |
| `feedback_config.yaml` | Tickets e SAC |
| `guardrails_config.yaml` | Escopo e políticas |
| `style_config.yaml` | Tom e estilo de comunicação |

Referência completa: [templates/standard/](../../templates/standard/README.md).

## Nota para o Copilot

Criar a pasta do cliente e o arquivo `triage_config.yaml` mínimo se ainda não existirem. Os demais arquivos YAML são opcionais e podem ser adicionados depois conforme a necessidade do projeto.
