---
type: bug
status: todo
id: bug-issue-6
title: "issue #6: guardian backup falla con exit 1 (traceback) si dos carpetas origen comparten basename"
parent: story-imported-issues
labels: [bug]
created: "2026-09-13"
updated: "2026-09-13"
issue: 6
---
## Pasos para reproducir
1. Configurar `guardian.toml` con dos orígenes cuyo basename coincide:

```toml
[[sources]]
path = "/tmp/proyecto-a/data"

[[sources]]
path = "/tmp/proyecto-b/data"

[destination]
path = "/tmp/backups"
```

2. `uv run guardian backup`

## Comportamiento observado
La segunda corrida de copia escribe sobre la primera: `<backup>/data/` recibe ambos árboles mezclados y el `manifest.json` queda con entradas duplicadas de `destination` (silenciosamente). Si además hay un archivo con la misma ruta relativa en ambos orígenes, el del segundo origen pisa al primero **sin advertir** y el manifiesto declara un hash que no corresponde a ningún archivo único.

## Comportamiento esperado
O bien namespacing sin colisión (`proyecto-a--data/`) o un error de configuración claro en `load_config` (exit 2), nunca un backup ambiguo con exit 0.

## Entorno
- guardian 0.1.0, Python 3.13.15, Linux x86_64
> imported from issue #6
