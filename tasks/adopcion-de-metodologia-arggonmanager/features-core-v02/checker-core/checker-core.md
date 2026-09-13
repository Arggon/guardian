---
type: story
status: done
id: checker-core
title: "Checker core: corrida supervisable con resumen por origen y exit codes"
assignee: Arggon
branch: feat/checker-core
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

- [x] `guardian backup` con un origen fallido termina con exit 4 y reporta qué origen falló.
- [x] Los orígenes sanos de esa misma corrida quedan copiados y verificados en el manifiesto.
- [x] Exit 0 cuando todos los orígenes están ok; 2 config; 3 integridad (comportamiento previo intacto).
- [x] Tests en tests/test_backup.py cubren los tres estados con tmp_path (sin FS real).

## Notes

Referencia: issue GitHub #1. Fix de bug-issue-6 (colisión de basenames) NO entra
en esta story: va como fix separado (un PR por item).

## Notes

- 2026-09-13 (implementación): `run_backup` ya no aborta ante un origen fallido
  (HashMismatch/OSError): cada origen produce un `SourceReport` con `status`
  ok/failed y `error` ("Tipo: mensaje"), volcado al manifiesto (`sources[i].status`
  y `sources[i].error` — docs/FORMAT.md actualizado en el mismo PR). Exit codes:
  0 todos ok · 2 config (igual que antes) · 3 integridad total (todos los orígenes
  HashMismatch; v0.1 un solo origen mantiene el comportamiento) · 4 corrida parcial.
  Tabla de exit codes documentada en el epílogo de `guardian backup --help` y en
  docs/FORMAT.md. Invariantes intactos: dry-run no escribe nada (con o sin fallos),
  nunca se pisan backups previos, SHA-256 doble origen+copia. Fallback de CLI por
  HashMismatch fuera del flujo de run_backup fue removido (run_backup ya no lanza).
  Suite: 27 passed, ruff limpio, arggon validate ok. Corrida parcial queda como
  manifiesto válido con entradas `failed` — verify/rotate/restore (issues #2-#4)
  decidirán cómo tratarlas.

### 2026-09-13 @Arggon
implementación completa en PR https://github.com/Arggon/guardian/pull/7: run_backup ya no aborta por origen fallido (SourceReport con status ok/failed + error 'Tipo: mensaje' volcado al manifiesto); exit codes 0/2/3/4 (3 = todos los orígenes HashMismatch, v0.1 un solo origen igual que antes; 4 = parcial) documentados en epílogo de backup --help y docs/FORMAT.md (mismo commit). Invariantes intactos (dry-run no escribe, no pisa backups, SHA-256 doble). 6 tests nuevos con monkeypatch de hash_file; suite 27 passed, ruff limpio, validate ok:true.
