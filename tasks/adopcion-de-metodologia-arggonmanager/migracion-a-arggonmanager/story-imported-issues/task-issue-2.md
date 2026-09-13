---
type: task
status: todo
id: task-issue-2
title: "issue #2: Verificación de integridad: comando guardian verify"
parent: story-imported-issues
labels: []
created: "2026-09-13"
updated: "2026-09-13"
issue: 2
---
## Objetivo
`guardian verify --backup <id|latest>`: recomputar SHA-256 de cada archivo del backup y comparar contra `manifest.json` (formato en docs/FORMAT.md).

## Detalles
- Un backup sin manifest.json debe reportarse como **incompleto** y no verificable (invariante 1 de FORMAT.md).
- Reporte por archivo: ok / hash-mismatch / faltante.
- Exit 0 si todo ok, 3 si hay mismatch.

## Criterio de aceptación
- Corromper un byte de un archivo respaldeado y verificar que `guardian verify` lo detecta con exit 3.
> imported from issue #2
