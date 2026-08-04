# 🔁 Exemplo: Single Reply Mode

Este exemplo demonstra como configurar o **Single Reply Mode** no AtendentePro.

## O que é Single Reply Mode?

Quando ativado, o agente responde **apenas uma vez** e automaticamente transfere de volta para o Triage. Isso evita que a conversa fique "presa" em um agente específico.

## Quando Usar

| Cenário | Recomendação |
|---------|--------------|
| **Chatbots de alto volume** | ✅ Ativar para respostas rápidas |
| **FAQ simples** | ✅ Knowledge com single_reply |
| **Coleta de dados** | ❌ Interview precisa múltiplas interações |
| **Onboarding** | ❌ Precisa guiar o usuário em etapas |
| **Confirmações** | ✅ Confirma e volta ao Triage |

## Arquivos

- `single_reply_config.yaml` - Configuração via YAML
- `example_via_code.py` - Configuração via código Python
- `example_via_yaml.py` - Carregamento de configuração YAML
- `run_example.py` - Script para executar os exemplos

## Executando

```bash
# Configurar variáveis de ambiente
export OPENAI_API_KEY=sk-...
export ATENDENTEPRO_LICENSE_KEY=ATP_...

# Executar
python run_example.py
```

## Comportamento

### Com single_reply=True:

```
[Usuário: "Qual o preço do produto X?"]
     ↓
[Triage] → detecta consulta de conhecimento
     ↓
[Knowledge Agent] → responde com preço
     ↓
[Triage] ← retorno AUTOMÁTICO
     ↓
[Usuário: "E o produto Y?"]
     ↓
[Triage] → nova análise...
```

### Com single_reply=False (padrão):

```
[Usuário: "Qual o preço do produto X?"]
     ↓
[Triage] → detecta consulta
     ↓
[Knowledge Agent] → responde
     ↓
[Usuário: "E o produto Y?"]
     ↓
[Knowledge Agent] → continua no mesmo agente
     ↓
[Usuário: "Quero falar com atendente"]
     ↓
[Knowledge Agent] → handoff para Escalation
```

## Configuração Recomendada

Para a maioria dos casos de uso, recomendamos:

```yaml
global: false  # Não ativar globalmente

agents:
  knowledge: true      # FAQ: responde e volta
  confirmation: true   # Confirma e volta
  answer: true         # Responde e volta
  
  interview: false     # Precisa coletar dados
  onboarding: false    # Precisa guiar usuário
  flow: false          # Apresenta opções
```
