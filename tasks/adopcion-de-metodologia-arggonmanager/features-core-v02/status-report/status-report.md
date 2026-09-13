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

### 2026-09-13 @Arggon
Handoff MCP-first — implementación completa.

QUÉ: `guardian status [--config] [--json]` (lectura pura del destino): lista dirs YYYYMMDD-HHMMSS con id, created_at del manifiesto, archivos, bytes y `complete` (manifiesto presente y parseable; sin manifiesto cuenta en disco y marca incompleto). Exit 0 ok / 2 config. Archivos: guardian/status.py, guardian/cli.py, tests/test_status.py (tmp_path + snapshot pure-read). Helper MCP: tools/mcp_client.py. Doc: docs/mcp-capabilities.md.

PR: https://github.com/Arggon/guardian/pull/9 (head af4c8b5, branch feat/status-report). pytest 34 passed, ruff limpio, arggon validate --json ok. Acceptance marcada en el body (editado a mano: el body NO es editable por MCP).

3 hallazgos del experimento MCP:
1. Paridad total de lectura/escritura de tracker por MCP (arggon_list con filtros, arggon_update de frontmatter — labels probado y revertido—, arggon_comment de este handoff); pero NO hay arggon_get ni next --ready: leer un item puntual o sugerir claimable requiere traer la lista completa y razonar en el cliente.
2. El claim con `start --worktree` (branch+worktree+push) NO es posible por MCP (ausente en tools/list): el claim de esta story lo tomó el coordinador con CLI. Igual que validate, spec/plan, board, report --trend, sync, import-issues, adopt y cleanup.
3. El body del item no es editable por MCP (arggon_update solo toca frontmatter): los checkboxes de Acceptance solo se marcan editando el archivo y commiteando; arggon_comment agrega pero no modifica.
