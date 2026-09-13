---
type: story
status: in_progress
id: status-report
title: Reporte de estado de backups (guardian status --json)
assignee: Arggon
branch: feat/status-report
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
claimed_at: "2026-09-13T18:17:11.549Z"
depends_on: [checker-core]
worktree_path: /home/arggon/Projects/guardian-status-report
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

- [x] `guardian status` (humano) lista cada backup con id, archivos, bytes y marca incompleto si falta manifiesto.
- [x] `guardian status --json` emite `{backups: [{id, created_at, files, bytes, complete}]}` en stdout.
- [x] Nunca escribe en el destino (pure read, test que lo verifica).
- [x] Destino vacío → lista vacía y exit 0 (no error).
- [x] Tests con tmp_path.

## Notes

Esta story se ejecuta MCP-FIRST: todas las interacciones con el tracker
(arggon_list / arggon_update) se hacen vía `arggon mcp` (JSON-RPC stdio), y se
documenta qué se puede y qué no hacer solo por MCP. Depende de checker-core
(porque interpreta manifiestos producidos por la corrida supervisable).

### Resumen del experimento MCP-first (2026-09-13)

Story ejecutada MCP-first: tracker exclusivamente vía `arggon mcp`
(JSON-RPC stdio), usando el helper `tools/mcp_client.py`. Detalle completo en
docs/mcp-capabilities.md.

- Tools disponibles (`tools/list`): `arggon_list`, `arggon_create`,
  `arggon_update`, `arggon_comment`. Sin `arggon_get`.
- SÍ por MCP (con evidencia): `arggon_list` con filtros
  (`parent:features-core-v02`, `status:in_progress`), `arggon_update` de
  labels probado y revertido (`mcp-test` → `[]`), `arggon_comment` (este
  experimento y el handoff final).
- NO por MCP (ausente en tools/list): claim/start --worktree (el claim de esta
  story lo tomó el coordinador con CLI), validate, spec/plan, playbooks,
  board, report --trend, sync, import-issues, adopt, cleanup, next --ready.
- Hallazgo clave: el **body del item no es editable por MCP**
  (`arggon_update` solo toca frontmatter); los checkboxes de Acceptance se
  marcan editando este archivo y commiteando con git.
- Conclusión: la mitad tracker (leer grafo, crear, actualizar frontmatter,
  comentar) tiene paridad total por MCP; falta cobertura para todo lo que
  toca git/gh/documentos.
