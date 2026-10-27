# 18 — Scheduling: API publica de `SchedulingConfig` para generators externos

A partir do issue [#270](https://github.com/BeMonkAI/atendentepro/issues/270), os modelos canonicos do scheduling sao exportados no namespace publico da lib e ganham helper de serializacao round-trippable. Util para clientes que produzem `scheduling_config.yaml` dinamicamente (Supabase edge functions, scripts batch, CMS exporters) — em vez de re-implementar a logica de defaults da lib, basta construir o modelo e dumpa-lo.

## 18.1 — Exports publicos

Os modelos `SchedulingConfig` e `Location` (e o TypedDict `LocationDict`) agora sao acessiveis tanto no top-level quanto no namespace `atendentepro.templates`:

```python
# Top-level (recomendado)
from atendentepro import SchedulingConfig, Location, LocationDict

# Equivalente
from atendentepro.templates import SchedulingConfig, Location, LocationDict
```

`SchedulingConfig` carrega os defaults canonicos da lib (`allow_create=True`, `allow_reschedule=True`, `allow_cancel=True`, `locations=[]`).

`LocationDict` (issue #269) e um TypedDict que documenta o shape esperado quando o consumidor prefere dicts crus (gera autocomplete + type-check no mypy/pyright sem importar Pydantic):

```python
from atendentepro import LocationDict

loc: LocationDict = {"id": "loc_a", "name": "Main", "city": "Sao Paulo"}
# Type-checker pega "address" → "address_full" typos aqui, no client code.
```

Required: `id`, `name`. Optional (`NotRequired`): `city`, `address_full`, `maps_url`, `window_start`, `window_end`.

## 18.2 — `to_yaml_dict()` round-trippable

Tanto `SchedulingConfig` quanto `Location` expoem `to_yaml_dict()` que retorna um `dict` no shape exato que `SchedulingConfig.load(path)` espera. Serializavel direto via `yaml.safe_dump`.

```python
import yaml
from atendentepro import SchedulingConfig, Location

cfg = SchedulingConfig(
    about="Clinica X",
    allow_reschedule=False,
    locations=[
        Location(id="loc_a", name="Unidade Central", city="Sao Paulo"),
        Location(id="loc_b", name="Filial Norte"),  # campos opcionais omitidos
    ],
)

with open("scheduling_config.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(cfg.to_yaml_dict(), f, sort_keys=False)
```

Garantia: `SchedulingConfig.load("scheduling_config.yaml") == cfg` (round-trip estavel).

## 18.3 — Por que isso importa

Sem essa API publica, generators externos precisam:

1. **Re-implementar defaults** — ler colunas do banco e aplicar `True` quando ausentes, replicando a logica que ja vive em `SchedulingConfig.load`. Toda vez que a lib evolui (ex: nova chave em v0.31.0 com `allow_*`), o generator dessincroniza.
2. **Tipar manualmente** os campos opcionais de `Location` (ver [#268](https://github.com/BeMonkAI/atendentepro/issues/268)) para evitar emitir `null` em campos que eram `str`.
3. **Descobrir empiricamente** quais campos sao consumidos hoje vs aceitos sem warning (`professionals`, `appointment_types`).

Com `to_yaml_dict()`, esses tres pontos passam a ser responsabilidade da lib. O generator constroi o modelo e dumpa — qualquer mudanca interna na lib aparece automaticamente.

## 18.4 — Campos emitidos vs aceitos no YAML

`SchedulingConfig.to_yaml_dict()` emite apenas as chaves que a lib **consome ativamente** hoje:

| Chave | Emitida? | Observacao |
|---|---|---|
| `about` | sim | string |
| `template` | sim | string |
| `format` | sim | string |
| `allow_create` | sim | default `True` |
| `allow_reschedule` | sim | default `True` |
| `allow_cancel` | sim | default `True` |
| `locations` | sim | lista de `Location.to_yaml_dict()` |
| `professionals` | nao | aceito no `load` (sem warning), reservado para extensao futura |
| `appointment_types` | nao | idem |

`Location.to_yaml_dict()` sempre emite `id` + `name` (requeridos) e omite campos opcionais quando `None` para manter o YAML limpo — `_location_field` no prompt builder ja trata omitidos e `None` como equivalentes.

## 18.5 — Padrao recomendado para generators externos

```python
# 1. Carregar dados do banco / CMS / API.
clinic = fetch_clinic_from_db(clinic_id)

# 2. Mapear para o modelo Pydantic publico.
cfg = SchedulingConfig(
    about=clinic.scheduling_about or "",
    allow_create=clinic.scheduling_allow_create,
    allow_reschedule=clinic.scheduling_allow_reschedule,
    allow_cancel=clinic.scheduling_allow_cancel,
    locations=[
        Location(
            id=loc.code,
            name=loc.name,
            city=loc.city,
            address_full=loc.address,
            maps_url=loc.maps_url,
            window_start=loc.window_start,  # `None` aceito (issue #268)
            window_end=loc.window_end,
        )
        for loc in clinic.locations
    ],
)

# 3. Dumpar para YAML round-trippable.
import yaml
yaml_str = yaml.safe_dump(cfg.to_yaml_dict(), sort_keys=False, allow_unicode=True)
```

## 18.6 — Versionamento

Disponivel a partir da v0.38.0. Para versoes anteriores, generators precisam continuar replicando os defaults manualmente.
