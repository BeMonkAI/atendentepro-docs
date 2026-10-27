# 31 — Exportar a topologia declarada da rede

Issue #585 — a visão "Flow" do MonkAI Hub só mostra a topologia **observada** nos traces. Handoffs configurados que nunca dispararam, tools declaradas que nunca foram chamadas e guardrails não aparecem. `export_network_topology(network)` devolve a topologia **declarada** como um `dict` estável e serializável em JSON, para o consumidor enviar ao Hub no startup.

O envio (endpoint de upload) fica no `monkai-trace`, não nesta lib.

## 31.1 — Uso

```python
import json
from atendentepro import create_standard_network, export_network_topology

network = create_standard_network(templates_root=TEMPLATES, client="meu_cliente")
topology = export_network_topology(network)
payload = json.dumps(topology, sort_keys=True)  # mesma rede -> mesmos bytes
```

Aceita `AgentNetwork` (redes `create_standard_network` e `create_custom_network`) e `ParallelNetwork` (`create_parallel_network`). Qualquer outro objeto levanta `TypeError`.

## 31.2 — Exemplo de saída (recortado)

```json
{
  "agents": {
    "triage": {
      "can_call": [],
      "exposed_to_user": true,
      "handoffs": ["escalation", "flow", "knowledge"],
      "has_knowledge_tool": false,
      "input_guardrails": ["triage_agent_guardrail"],
      "instructions_sha256": "78ffac7a93825012",
      "is_entry_point": true,
      "model": "gpt-4.1",
      "name": "Triage Agent",
      "scope_configured": true,
      "tools": []
    }
  },
  "client": "meu_cliente",
  "entry_point": "triage",
  "network_type": "standard",
  "schema_version": 1
}
```

## 31.3 — Campos

| Campo | Significado |
|---|---|
| `schema_version` | Versão do formato (hoje `1`). Muda só em quebra de contrato. |
| `network_type` | `standard` (AgentNetwork) ou `parallel` (ParallelNetwork). |
| `client` | Chave do cliente (`current_client`), só em `standard`. |
| `entry_point` | Agente que recebe a mensagem do usuário (`triage`); `null` em `parallel`. |
| `fanout` / `coordinator` | Só em `parallel`: agentes do fanout (ordenados) e o coordenador. |
| `agents.<chave>` | Uma entrada por agente habilitado, pela chave estável (`triage`, `flow`...). Agente desligado (`include_*=False`) não aparece. |
| `name` | Nome exibido, o mesmo que aparece nos traces. |
| `model` | Id do modelo quando é string; `null` quando é um objeto `Model`. |
| `tools` | Nomes das tools, ordenados. |
| `has_knowledge_tool` | `true` quando o agente tem a tool de RAG (`go_to_rag`). |
| `handoffs` | Chaves dos agentes para os quais pode fazer handoff, ordenadas. |
| `input_guardrails` | Nomes dos guardrails de entrada. |
| `scope_configured` | `true` quando há escopo em `guardrails_config.yaml::agent_scopes` (validador LLM de escopo ativo). |
| `exposed_to_user` / `can_call` | Metadados multi-agente (`multiagent_config.yaml`). Sem metadados: `true` / `[]`. |
| `is_entry_point` | `true` só no agente de entrada. |
| `instructions_sha256` | 16 primeiros hex do SHA-256 do prompt. Veja abaixo. |

## 31.4 — O que nunca sai

O export **nunca** inclui texto de prompt/instructions, chaves de API, base URLs ou dados de usuário. Para o Hub detectar que um prompt mudou sem ver o conteúdo, cada agente leva `instructions_sha256`: um prefixo de 16 caracteres do SHA-256 do texto das instructions. Prompt mudou, hash mudou. Instructions dinâmicas (callable) dão `null`.

## 31.5 — Determinismo

Listas são ordenadas e o `dict` é montado a partir da configuração, sem timestamp nem id de processo. A mesma rede gera um `json.dumps(..., sort_keys=True)` idêntico byte a byte, então o consumidor pode usar o hash do payload para só reenviar quando algo mudar.
