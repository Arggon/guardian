---
type: task
status: todo
id: task-issue-4
title: "issue #4: Restore: guardian restore <backup> --dest <ruta>"
parent: story-imported-issues
labels: []
created: "2026-09-13"
updated: "2026-09-13"
issue: 4
---
## Objetivo
Restaurar un backup verificado a una ruta de destino, usando el manifiesto como fuente de verdad.

## Detalles
- `guardian restore <backup_id|latest> --dest <ruta>`: copia de vuelta `destination -> dest/<path origen>`.
- Verificación SHA-256 de cada archivo restaurado contra el manifiesto (mismo estándar que backup).
- Por seguridad: `--dest` no puede ser un directorio existente no vacío sin `--overwrite`.

## Criterio de aceptación
- Backup → borrar origen → restore → diff -r sin diferencias.
> imported from issue #4
