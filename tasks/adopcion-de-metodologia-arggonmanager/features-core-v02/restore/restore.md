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
claimed_at: "2026-09-13T18:12:24.609Z"
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
