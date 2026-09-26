# Exemplo: AgentStyle - Tom e Estilo Customizáveis

Este exemplo demonstra como personalizar o tom e estilo de comunicação dos agentes usando `AgentStyle`.

## 📁 Estrutura

```
agent_style/
├── README.md                    # Esta documentação
├── style_config.yaml            # Configuração via YAML
├── example_via_code.py          # Exemplo programático
├── example_via_yaml.py          # Exemplo usando YAML
└── run_example.py               # Script para testar
```

## 🎨 O que é AgentStyle?

`AgentStyle` permite personalizar como os agentes se comunicam:

| Parâmetro | Valores | Descrição |
|-----------|---------|-----------|
| `tone` | Texto livre | Tom da conversa (ex: "profissional", "empático") |
| `language_style` | `formal`, `informal`, `neutro` | Nível de formalidade |
| `response_length` | `conciso`, `moderado`, `detalhado` | Tamanho das respostas |
| `custom_rules` | Texto livre | Regras personalizadas |

## Carregamento automático do YAML

Com `load_style_from_template=True` (padrão), `create_standard_network()` aplica o `style_config.yaml` do diretório do cliente junto com estilos passados em código — **código sobrescreve o YAML** quando o mesmo agente está definido nos dois.

## 🚀 Uso Via Código

```python
from atendentepro import create_standard_network, AgentStyle
from pathlib import Path

# Estilo global (todos os agentes)
global_style = AgentStyle(
    tone="profissional e consultivo",
    language_style="formal",
    response_length="moderado",
)

# Estilos específicos por agente
network = create_standard_network(
    templates_root=Path("./templates"),
    client="standard",
    global_style=global_style,
    agent_styles={
        "escalation": AgentStyle(tone="empático"),
        "knowledge": AgentStyle(response_length="detalhado"),
    },
)
```

## 📄 Uso Via YAML

Crie um arquivo `style_config.yaml` na pasta do seu cliente:

```yaml
global:
  tone: "profissional e cordial"
  language_style: "formal"
  response_length: "moderado"

agents:
  escalation:
    tone: "empático e tranquilizador"
  knowledge:
    tone: "didático"
    response_length: "detalhado"
```

## ▶️ Executar Exemplo

```bash
# Via código
python example_via_code.py

# Via YAML
python example_via_yaml.py

# Teste interativo
python run_example.py
```

## 💡 Casos de Uso

### Atendimento Formal (Banco, Jurídico)
```python
AgentStyle(
    tone="profissional e respeitoso",
    language_style="formal",
    response_length="detalhado",
    custom_rules="Use sempre 'senhor/senhora'. Cite normas quando aplicável."
)
```

### Suporte Técnico Amigável
```python
AgentStyle(
    tone="amigável e prestativo",
    language_style="informal",
    response_length="conciso",
    custom_rules="Use emojis ocasionalmente. Seja direto nas soluções."
)
```

### SAC Empático (Reclamações)
```python
AgentStyle(
    tone="empático e acolhedor",
    language_style="formal",
    response_length="moderado",
    custom_rules="Sempre demonstre compreensão. Peça desculpas quando apropriado."
)
```
