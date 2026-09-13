---
type: story
status: in_progress
id: restore
title: "guardian restore: reconstrucción verificada desde un backup"
assignee: Arggon
branch: feat/restore
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
claimed_at: "2026-09-13T18:21:18.621Z"
depends_on: [verify]
worktree_path: /home/arggon/Projects/guardian-restore
---
<!--
  Placement (v0): tasks/adopcion-de-metodologia-arggonmanager/features-core-v02/restore/restore.md (story index; required).
  parent MUST be the epic id. Optional style prefixes (e.g. story-) are not type discriminators.
-->

# guardian restore: reconstrucción verificada desde un backup

## Context

Spec: docs/specs/spec-backup-pipeline-v2-001.md (issue GitHub #4). `guardian
restore <backup_id|latest> --dest <ruta> [--overwrite]` reconstruye los orígenes
desde un backup, re-verificando cada archivo contra el manifiesto.

## Acceptance

- [ ] Backup → borrar origen → restore → `diff -r` sin diferencias.
- [ ] Cada archivo restaurado se re-verifica contra el manifiesto; mismatch → exit 3 y archivo reportado.
- [ ] `--dest` existente y no vacío sin `--overwrite` → exit 2 con mensaje claro.
- [ ] `latest` resuelve igual que en verify.
- [ ] Tests con tmp_path cubren restore limpio, mismatch y protección de destino no vacío.

## Notes

Depende de verify: reutiliza sus helpers de verificación hash-manifiesto.
> stolen 2026-09-13 by Arggon: chaos test: agente intenta robar el claim propio abandonado

### 2026-09-13 @Arggon
HANDOFF (test de caos — agente abandonó a mitad de implementación):

QUÉ ENCONTRARÁS EN EL WORKTREE (feat/restore, sin commitear):
- guardian/restore.py WIP ~50%: restore_backup() copia y re-verifica SHA-256 contra el manifiesto; RestoreError/RestoreHashMismatch definidos; resolve_backup_dir() solo resuelve ids explícitos.
- FALTA: protección de --dest no vacío sin --overwrite, resolución de 'latest', wiring del subcomando en cli.py, tests/test_restore.py, actualización de README/docs.

HALLAZGOS DEL EXPERIMENTO (coordinador):
1. El claim vive SOLO en este branch: desde main la task se ve todo/claimed_at null (start.ts:431-448 commitea el claim en el worktree) → list --stale desde main es ciego a este abandono; hay que correrlo desde el worktree.
2. update --steal por CLI NO fue negado al agente (ok:true, claimed_at refrescado 18:21:18Z): el CLI nunca pasa agent:true (cli.ts/update.ts; solo mcp-server.ts:289 lo hace). Vía MCP el schema de arggon_update ni siquiera expone steal → la regla human-only del skill solo se aplica (parcialmente) por MCP.

PARA EL HUMANO: decidir --steal (desde este worktree) o descartar el branch. El árbol tiene trabajo WIP no commiteado a propósito (simulación de agente muerto).
