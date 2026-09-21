# Passo 3: Ativação e primeira rede

## Objetivo

Ativar a licença da biblioteca, criar a rede de agentes e executar o primeiro run (conversa com o triage).

## Passo 3.1: Ativar a licença

No código de entrada da aplicação (main, app ou ponto onde a rede será usada), chamar `activate()` **antes** de qualquer uso da rede. Use o token do ambiente ou do .env:

```python
import os
from dotenv import load_dotenv
from atendentepro import activate

load_dotenv()
activate(os.getenv("ATENDENTEPRO_LICENSE_KEY"))
```

Ou, se preferir passar o token diretamente (evitar em produção):

```python
from atendentepro import activate
activate("ATP_seu-token-aqui")
```

## Passo 3.2: Definir pasta de templates e nome do cliente

- `templates_root`: caminho da pasta que contém as subpastas de configuração por cliente (ex.: `Path("config")` ou `Path("./templates")`).
- `client`: nome da subpasta do cliente (ex.: `"meu_cliente"` ou `"standard"`).

A pasta efetiva será `templates_root / client` (ex.: `config/meu_cliente`). Ela deve existir e conter pelo menos `triage_config.yaml` (ver [04_templates_obrigatorios.md](04_templates_obrigatorios.md)).

## Passo 3.3: Criar a rede

```python
from pathlib import Path
from atendentepro import create_standard_network

network = create_standard_network(
    templates_root=Path("[CAMINHO_PASTA_TEMPLATES]"),
    client="[NOME_CLIENTE]",
)
```

Exemplo concreto:

```python
network = create_standard_network(
    templates_root=Path("./config"),
    client="meu_cliente",
)
```

## Passo 3.4: Primeiro run

Executar o agente de triage com uma mensagem de teste. O retorno é um objeto com `final_output` (texto da resposta).

```python
import asyncio
from agents import Runner

async def main():
    messages = [{"role": "user", "content": "Olá, preciso de ajuda"}]
    result = await Runner.run(network.triage, messages)
    print(result.final_output)

asyncio.run(main())
```

Se usar `run_with_memory` (módulo de memória), substitua `Runner.run(network.triage, messages)` por `run_with_memory(network, network.triage, messages)` — ver [05_opcionais_memoria.md](05_opcionais_memoria.md).

## Nota para o Copilot

Garantir que `activate()` seja chamado antes de qualquer uso da rede (create_standard_network, Runner.run, run_with_memory). Criar a rede com `templates_root` e `client` apontando para a pasta de configuração do cliente que contém `triage_config.yaml`.
