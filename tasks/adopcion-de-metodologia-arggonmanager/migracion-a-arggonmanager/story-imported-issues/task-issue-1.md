---
type: task
status: todo
id: task-issue-1
title: "issue #1: Checker core: completar el motor de backup como comando supervisable"
parent: story-imported-issues
labels: []
created: "2026-09-13"
updated: "2026-09-13"
issue: 1
---
## Objetivo
Convertir el motor de copia actual (`guardian/copier.py` + `guardian/backup.py`) en el **checker core**: una corrida de backup supervisable que reporte estado por carpeta (ok / parcial / fallida) y exit code diferenciado.

## Alcance
- Resumen por origen: archivos copiados, bytes, errores.
- Exit codes: 0 ok, 2 config, 3 integridad, 4 parcial (ya existen 2 y 3).
- No reescribir backups existentes (invariante timestamps).

## Criterio de aceptación
- `guardian backup` sobre 2 orígenes con uno corrupto termina con exit 4 y reporta el origen fallido.
- Suite pytest cubre los tres estados.
> imported from issue #1
