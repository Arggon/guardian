---
type: story
status: todo
id: rotacion
title: Rotación keep-last-N de backups viejos
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
depends_on: [verify]
---
<!--
  Placement (v0): tasks/adopcion-de-metodologia-arggonmanager/features-core-v02/rotacion/rotacion.md (story index; required).
  parent MUST be the epic id. Optional style prefixes (e.g. story-) are not type discriminators.
-->

# Rotación keep-last-N de backups viejos

## Context

Spec: docs/specs/spec-backup-pipeline-v2-001.md (issue GitHub #3; decisión en
docs/DECISIONS.md §3). `guardian rotate [--keep N]` borra los backups completos
más viejos dejando keep_last (default de config). Solo lectura de manifiestos +
unlink de directorios elegidos.

## Acceptance

- [ ] Con keep_last=3 y 5 backups con manifiesto quedan exactamente los 3 más nuevos.
- [ ] Un directorio con patrón timestamp pero SIN manifest.json NO se borra (posible corrida en curso) y se reporta.
- [ ] Directorios que no matchean `YYYYMMDD-HHMMSS` (p. ej. backup/ de arggon) se ignoran siempre.
- [ ] `--keep N` overrideea config; N < 1 es error de config (exit 2).
- [ ] Nunca borra el backup más nuevo, incluso si keep_last fuera 0→error.
- [ ] Tests con tmp_path (crear 5 backups falsos con manifests) cubren cada regla.

## Notes

Depende de verify solo por el helper de detección de backup completo
(manifiesto válido), no por el hash-walk completo.
