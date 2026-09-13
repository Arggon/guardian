---
type: story
status: done
id: runbooks
title: Runbooks operativos del pipeline de backup
assignee: Arggon
branch: feat/runbooks
parent: features-core-v02
labels: []
created: "2026-09-13"
updated: "2026-09-13"
worktree_path: null
---
<!--
  Placement (v0): tasks/adopcion-de-metodologia-arggonmanager/features-core-v02/runbooks/runbooks.md (story index; required).
  parent MUST be the epic id. Optional style prefixes (e.g. story-) are not type discriminators.
-->

# Runbooks operativos del pipeline de backup

## Context

<!-- Why this story exists. -->

## Acceptance

- [x] emergency-restore.md
- [x] corrupt-rotation.md
- [x] disk-full.md
- [x] expired-credentials.md
- [x] partial-backup.md
- [x] hash-false-green.md

## Notes

- 2026-09-13: los 6 runbooks escritos en docs/runbooks/ con estructura Trigger → Diagnosis → Mitigation → Escalation → Rollback, comandos reales del proyecto (uv run guardian backup, manifest.json, sha256sum, du/df) y citas a invariantes de FORMAT.md/ARCHITECTURE.md.
- Los subcomandos no implementados (verify #2, rotate #3, notificación #5, exit 4 de partial) se referencian como comandos planificados con la alternativa manual de hoy entre paréntesis.
- Índice actualizado en docs/runbooks/README.md (un bullet por runbook).

### 2026-09-13 @Arggon
runbooks listos en PR https://github.com/Arggon/guardian/pull/8: emergency-restore.md (restore manual con cp + sha256 contra manifest.json), corrupt-rotation.md (qué borrar y qué nunca: más nuevo y dirs sin manifiesto), disk-full.md (ENOSPC: df/du, rotación guiada, reanudar), expired-credentials.md (rotar GUARDIAN_TELEGRAM_TOKEN/CHAT_ID; notificación nunca tumba el backup), partial-backup.md (exit 4 planificado: estado por origen, nunca rotar parcial a ciegas), hash-false-green.md (auditar con sha256sum de sistema + re-hash posterior). Decisiones: subcomandos no implementados (verify #2, rotate #3, notificación #5, exit 4) referenciados como planificados con alternativa manual hoy entre paréntesis; invariantes de FORMAT.md/ARCHITECTURE.md citados en cada runbook.
