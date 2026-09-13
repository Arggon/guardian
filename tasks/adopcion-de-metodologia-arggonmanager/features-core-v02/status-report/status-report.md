---
type: story
status: todo
id: status-report
title: Reporte de estado de backups (guardian status --json)
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
depends_on: [checker-core]
---
<!--
  Placement (v0): tasks/adopcion-de-metodologia-arggonmanager/features-core-v02/status-report/status-report.md (story index; required).
  parent MUST be the epic id. Optional style prefixes (e.g. story-) are not type discriminators.
-->

# Reporte de estado de backups (guardian status --json)

## Context

Spec: docs/specs/spec-backup-pipeline-v2-001.md (reporte local de estado,
relacionado con issue GitHub #5). `guardian status [--json]` lista los backups
del destino: id, fecha, archivos, bytes, presencia de manifiesto. Pure read.

## Acceptance

- [ ] `guardian status` (humano) lista cada backup con id, archivos, bytes y marca incompleto si falta manifiesto.
- [ ] `guardian status --json` emite `{backups: [{id, created_at, files, bytes, complete}]}` en stdout.
- [ ] Nunca escribe en el destino (pure read, test que lo verifica).
- [ ] Destino vacío → lista vacía y exit 0 (no error).
- [ ] Tests con tmp_path.

## Notes

Esta story se ejecuta MCP-FIRST: todas las interacciones con el tracker
(arggon_list / arggon_update) se hacen vía `arggon mcp` (JSON-RPC stdio), y se
documenta qué se puede y qué no hacer solo por MCP. Depende de checker-core
(porque interpreta manifiestos producidos por la corrida supervisable).
