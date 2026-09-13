---
type: task
status: todo
id: task-issue-3
title: "issue #3: Rotación keep-last-N: borrar backups viejos por timestamp"
parent: story-imported-issues
labels: []
created: "2026-09-13"
updated: "2026-09-13"
issue: 3
---
## Objetivo
Implementar la rotación simple decidida en docs/DECISIONS.md §3: ordenar directorios `YYYYMMDD-HHMMSS` del destino y borrar los más viejos dejando `destination.keep_last`.

## Reglas
- **Nunca** borrar el backup más nuevo ni directorios que no matcheen el patrón de timestamp (p. ej. `backup/` de ArggonManager no se toca).
- Nunca borrar un directorio sin `manifest.json` en la pasada de rotación (incompleto = posible backup en curso): reportarlo y saltarlo.

## Criterio de aceptación
- Con keep_last=3 y 5 backups, quedan exactamente los 3 más nuevos con manifest.json.
> imported from issue #3
