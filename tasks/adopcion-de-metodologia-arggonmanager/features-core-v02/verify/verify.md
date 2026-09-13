---
type: story
status: todo
id: verify
title: "guardian verify: verificación de integridad de backups contra manifiesto"
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
depends_on: [checker-core]
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

- [ ] `guardian verify --backup <id>` reporta ok por archivo y exit 0 cuando todo coincide.
- [ ] Un byte corrupto en un archivo respaldeado → reporta hash-mismatch con la ruta exacta y exit 3.
- [ ] Un archivo del manifiesto ausente en disco → reporta faltante y exit 3.
- [ ] Backup sin manifest.json → error "incompleto" (exit 3), nunca crash.
- [ ] `--backup latest` resuelve al timestamp más alto con manifiesto.
- [ ] Tests unitarios con tmp_path; pure read verificado por test (directorio sin cambios tras verify).

## Notes

Depende de checker-core: usa el resumen de corrida para decidir qué es un
backup completo (manifiesto presente = completo).
