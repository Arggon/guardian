---
type: story
status: done
id: rotacion
title: Rotación keep-last-N de backups viejos
assignee: Arggon
branch: feat/rotacion
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
depends_on: [verify]
worktree_path: /home/arggon/Projects/guardian-rotacion
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

- [x] Con keep_last=3 y 5 backups con manifiesto quedan exactamente los 3 más nuevos.
- [x] Un directorio con patrón timestamp pero SIN manifest.json NO se borra (posible corrida en curso) y se reporta.
- [x] Directorios que no matchean `YYYYMMDD-HHMMSS` (p. ej. backup/ de arggon) se ignoran siempre.
- [x] `--keep N` overrideea config; N < 1 es error de config (exit 2).
- [x] Nunca borra el backup más nuevo, incluso si keep_last fuera 0→error.
- [x] Tests con tmp_path (crear 5 backups falsos con manifests) cubren cada regla.

## Notes

Depende de verify solo por el helper de detección de backup completo
(manifiesto válido), no por el hash-walk completo.

- Implementación (2026-09-13): `guardian/rotation.py` (`run_rotation`, `eligible_ids`)
  + subcomando en `guardian/cli.py` con epílogo de exit codes (0 ok · 2 config, sin 3/4).
  Detección de completo vía `read_manifest` (presencia + parseo, no hash-walk).
  Conservador: manifiesto ausente o corrupto = skip, no elegible, no cuenta para
  keep_last. Sin patrón: ignorado en silencio. Tests: tests/test_rotation.py (10).

### 2026-09-13 @Arggon
implementación en PR https://github.com/Arggon/guardian/pull/11: `guardian rotate [--keep N]` en guardian/rotation.py + cli.py. Decisiones: (1) elegible = patrón YYYYMMDD-HHMMSS con manifiesto presente y parseable vía read_manifest (sin hash-walk, spec rotate); (2) manifiesto ausente o corrupto = SKIP conservador, no se borra ni cuenta para keep_last (cubre corrida en curso y manifest corrupto); (3) dirs sin patrón ignorados en silencio; (4) keep<1 (flag o config) → exit 2 sin borrar nada; exit codes 0/2 únicamente. Tests: tests/test_rotation.py (10, tmp_path + run_backup con now=). Resultados: pytest 61 passed, ruff limpio, arggon validate ok. Refs #3
