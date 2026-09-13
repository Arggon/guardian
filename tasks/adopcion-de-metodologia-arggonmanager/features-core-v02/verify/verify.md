---
type: story
status: in_progress
id: verify
title: "guardian verify: verificación de integridad de backups contra manifiesto"
assignee: Arggon
branch: feat/verify
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
claimed_at: "2026-09-13T18:17:09.467Z"
depends_on: [checker-core]
worktree_path: /home/arggon/Projects/guardian-verify
---
<!--
  Placement (v0): tasks/adopcion-de-metodologia-arggonmanager/features-core-v02/verify/verify.md (story index; required).
  parent MUST be the epic id. Optional style prefixes (e.g. story-) are not type discriminators.
-->

# guardian verify: verificación de integridad de backups contra manifiesto

## Context

Spec: docs/specs/spec-backup-pipeline-v2-001.md (issue GitHub #2). `guardian
verify [--backup <id|latest>]` recomputa SHA-256 de cada archivo contra el
manifest.json (formato docs/FORMAT.md). Pure read: nunca escribe.

## Acceptance

- [x] `guardian verify --backup <id>` reporta ok por archivo y exit 0 cuando todo coincide.
- [x] Un byte corrupto en un archivo respaldeado → reporta hash-mismatch con la ruta exacta y exit 3.
- [x] Un archivo del manifiesto ausente en disco → reporta faltante y exit 3.
- [x] Backup sin manifest.json → error "incompleto" (exit 3), nunca crash.
- [x] `--backup latest` resuelve al timestamp más alto con manifiesto.
- [x] Tests unitarios con tmp_path; pure read verificado por test (directorio sin cambios tras verify).

## Notes

- Implementación (2026-09-13): módulo nuevo `guardian/verify.py` (FileVerdict /
  VerifyResult frozen, `resolve_backup`, `verify_backup`, `run_verify`) +
  subcomando en `guardian/cli.py` con epílogo de exit codes, resumen por archivo
  (ok / hash-mismatch / faltante con rutas exactas) y conteo final. Exit codes:
  0 ok · 2 config o backup inexistente (incluye latest sin completos) · 3
  mismatch/faltante/manifiesto ausente o corrupto ("incompleto", nunca
  traceback). `--backup` default `latest`.
- **Fix a checker-core**: el campo `destination` del manifiesto se escribía
  relativo al subdirectorio del origen; docs/FORMAT.md exige `<nombre-origen>/<path>`
  relativo a la raíz del backup. Corregido en `run_backup` (dataclasses.replace)
  con test dedicado; verify depende de ese campo para ubicar cada archivo.
- `latest` ignora directorios sin `manifest.json` (test con dir más nuevo
  incompleto); sin completos → exit 2. Explicit id sin manifiesto → exit 3
  "incompleto" (el id existe, es la integridad la que falla).
- Pure read: test compara snapshot byte a byte del árbol del destino antes y
  después de verify. 17 tests nuevos en tests/test_verify.py; suite 44 verde +
  ruff limpio. Docs actualizadas en el mismo PR: FORMAT.md (exit codes de
  verify), README, ARCHITECTURE, CHANGELOG.

### 2026-09-13 @Arggon
implementación en PR https://github.com/Arggon/guardian/pull/10: módulo guardian/verify.py + subcomando en cli; latest = timestamp más alto con manifest.json (incompletos ignorados, sin completos → exit 2); id sin manifiesto → exit 3 'incompleto' (nunca traceback); pure read verificado por snapshot byte a byte del destino. Fix a checker-core: destination del manifiesto ahora relativo a la raíz del backup como exige docs/FORMAT.md. Resultados: 44 passed (17 nuevos), ruff limpio, arggon validate ok:true. Head: 24ae2ca.
