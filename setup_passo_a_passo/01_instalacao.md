# Passo 1: Instalação

## Objetivo

Instalar a biblioteca AtendentePro e, se necessário, os extras opcionais (tracing, memória, tuning).

## Pré-requisito

- Python 3.9 ou superior

## Comandos

**Instalação base:**

```bash
pip install atendentepro
```

**Extras opcionais (instalar apenas se o projeto precisar):**

```bash
# Monitoramento e tracing (recomendado em produção)
pip install atendentepro[tracing]

# Memória de contexto longo (conversas anteriores, GRKMemory)
pip install atendentepro[memory]

# Tuning / pós-treino (melhoria de YAMLs com base em feedback)
pip install atendentepro[tuning]
```

## Nota para o Copilot

Se o projeto precisar de memória de longo prazo (buscar e injetar conversas anteriores), instalar também `atendentepro[memory]`. Se precisar de tracing/monitoramento, instalar `atendentepro[tracing]`. Não instalar extras desnecessários.
