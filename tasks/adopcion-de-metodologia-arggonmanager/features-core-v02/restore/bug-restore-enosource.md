---
type: bug
status: done
id: bug-restore-enosource
title: "restore falla cuando la carpeta origen ya no existe: load_config exige fuentes existentes"
assignee: Arggon
branch: fix/bug-restore-enosource
parent: restore
labels: []
created: "2026-09-13"
updated: "2026-09-13"
worktree_path: /home/arggon/Projects/guardian-bug-restore-enosource
---
<!--
  Placement (v0): tasks/adopcion-de-metodologia-arggonmanager/features-core-v02/restore/bug-restore-enosource.md
  Leaves live only under a story. id is the filename stem: bug-restore-enosource.
  CLI `arggon create bug restore-enosource` adds the bug- prefix (do not pass it twice).
  parent MUST be the story id. Omit assignee when unassigned. Omit blocked_reason unless status is blocked.
-->

# restore falla cuando la carpeta origen ya no existe: load_config exige fuentes existentes

## Acceptance

- [x] Backup → borrar origen → `guardian restore` funciona y reconstruye el árbol (test de regresión `test_restore_works_after_source_deleted`).
- [x] backup/verify/status/rotate siguen exigiendo fuentes existentes (comportamiento intacto, 72 tests).

## Context

<!-- What went wrong / how to reproduce. -->

## Acceptance

- [ ] 

## Notes


## Notes

Causa raíz: `load_config` valida `is_dir()` de cada fuente; restore solo usa
`[destination]`. Fix: `load_config(..., require_sources_exist=False)` que solo el
subcomando restore usa. Detectado por la demo end-to-end post-merge de PR #12
(backup → rm origen → restore → exit 2 inesperado).
