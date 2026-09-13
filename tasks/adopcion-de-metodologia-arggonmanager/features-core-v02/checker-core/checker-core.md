---
type: story
status: todo
id: checker-core
title: "Checker core: corrida supervisable con resumen por origen y exit codes"
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
---
<!--
  Placement (v0): tasks/adopcion-de-metodologia-arggonmanager/features-core-v02/checker-core/checker-core.md (story index; required).
  parent MUST be the epic id. Optional style prefixes (e.g. story-) are not type discriminators.
-->

# Checker core: corrida supervisable con resumen por origen y exit codes

## Context

Spec: docs/specs/spec-backup-pipeline-v2-001.md (checker core, issue GitHub #1).
El motor de v0.1 copia pero no supervisa: esta story agrega resumen por origen
(ok/parcial/fallida con archivos, bytes, errores), exit 4 para corrida parcial
sin abortar los orígenes sanos, y el fix de reporte de errores por origen.

## Acceptance

- [ ] `guardian backup` con un origen fallido termina con exit 4 y reporta qué origen falló.
- [ ] Los orígenes sanos de esa misma corrida quedan copiados y verificados en el manifiesto.
- [ ] Exit 0 cuando todos los orígenes están ok; 2 config; 3 integridad (comportamiento previo intacto).
- [ ] Tests en tests/test_backup.py cubren los tres estados con tmp_path (sin FS real).

## Notes

Referencia: issue GitHub #1. Fix de bug-issue-6 (colisión de basenames) NO entra
en esta story: va como fix separado (un PR por item).
