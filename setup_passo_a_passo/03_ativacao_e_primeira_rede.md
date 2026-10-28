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

## Passo 3.5: Revogar uma licença vazada (sem trocar o segredo)

Cada token gerado a partir da versão com a issue #593 leva um id único (`jti`) dentro do payload assinado. Revogar = colocar esse `jti` numa denylist lida a cada validação. O segredo compartilhado (`ATENDENTEPRO_LICENSE_SECRET`) não muda e nenhum outro consumidor é afetado.

1. **Descobrir o `jti` do token vazado.** O `scripts/license_admin.py` imprime o `jti` na geração (registre junto do cliente). Se não estiver registrado, extraia do próprio token, lido de um arquivo (não cole o token na linha de comando, ele fica no histórico do shell):

   ```bash
   python3 -c 'import sys,json,base64; t=sys.stdin.read().strip(); print(json.loads(base64.urlsafe_b64decode(t[4:].rsplit(".",1)[0])).get("jti") or "SEM JTI (token legado)")' < token_vazado.txt
   ```

2. **Adicionar o `jti` à denylist** em todo processo que valida a licença (consumidores e servidor de validação `server/validation_server.py`, que usa a mesma validação local):

   ```bash
   # Opção A: variável de ambiente (ids separados por vírgula ou espaço)
   export ATENDENTEPRO_LICENSE_REVOKED="3f9c2a7b1d4e8f60,a1b2c3d4e5f60718"

   # Opção B: arquivo (um id por linha, comentários com #)
   echo "3f9c2a7b1d4e8f60  # vazado em 2026-10-23, chamado 123" >> /etc/atendentepro/revoked.txt
   export ATENDENTEPRO_LICENSE_REVOKED_FILE=/etc/atendentepro/revoked.txt
   ```

   As duas fontes se somam. Se `ATENDENTEPRO_LICENSE_REVOKED_FILE` apontar para um arquivo ilegível, todo token com `jti` é rejeitado (fail closed) e o erro vai para o log.

3. **Reiniciar os processos.** A denylist é lida em cada validação, mas um processo já ativado não revalida a licença; o reinício força a nova validação.

4. **Emitir um token novo** para o dono legítimo (validade padrão de 365 dias) e registrar o `jti` impresso:

   ```bash
   ATENDENTEPRO_LICENSE_SECRET=<do vault> python scripts/license_admin.py "NomeDoCliente"
   ```

5. **Conferir.** `activate()` com o token revogado levanta `LicenseRevokedError` (subclasse de `InvalidTokenError`) com a mensagem `... LICENCA REVOGADA (jti=<id>) ...`, e o log registra `Licenca revogada rejeitada (jti=<id>)`. Nem a mensagem nem o log contêm o token.

A denylist vale em todos os caminhos: validação local, resposta `valid=true` do endpoint online e fallback local quando o endpoint falha.

**Tokens legados (sem `jti`).** Tokens gerados antes da #593 continuam válidos exatamente como antes, mas não podem entrar na denylist: só deixam de valer por expiração ou por troca do segredo. Substitua-os por tokens novos (com `jti` e expiração) no próximo contato com cada cliente. Em produção com `ATENDENTEPRO_VALIDATION_URL`, o endpoint `/revoke` do servidor de validação continua revogando por token inteiro, inclusive legados.

## Nota para o Copilot

Garantir que `activate()` seja chamado antes de qualquer uso da rede (create_standard_network, Runner.run, run_with_memory). Criar a rede com `templates_root` e `client` apontando para a pasta de configuração do cliente que contém `triage_config.yaml`.
