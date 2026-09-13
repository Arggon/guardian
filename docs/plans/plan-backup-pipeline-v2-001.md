---
plan_id: backup-pipeline-v2-001
title: Plan for Pipeline de backup v0.2: checker core, verify, rotación, restore y status
spec: docs/specs/spec-backup-pipeline-v2-001.md
status: implemented
created: 2026-09-13
---

# Plan: Pipeline de backup v0.2 (backup-pipeline-v2-001)

Derived from `docs/specs/spec-backup-pipeline-v2-001.md`. Each task carries a
verifiable acceptance criterion and links back to the spec. Las historias viven
en el tracker (`tasks/adopcion-de-metodologia-arggonmanager/features-core-v02/`)
y el grafo de `depends_on` es la fuente de verdad del orden.

## Tasks

### T1: Checker core — story `checker-core`

- Resumen por origen en la corrida (ok/parcial/fallida), exit 4 en corrida
  parcial sin abortar orígenes sanos. Sin pisar lo de v0.1.
- **Acceptance:** ver checklist de `checker-core` (exit codes 0/2/3/4 + tests).

### T2: `guardian verify` — story `verify` (depends_on: checker-core)

- Recomputo SHA-256 contra manifiesto; ok/mismatch/faltante; pure read.
- **Acceptance:** checklist de `verify` (detección de byte corrupto con exit 3).

### T3: Rotación keep-last-N — story `rotacion` (depends_on: verify)

- Borrado de backups completos más viejos que keep_last; sin manifiesto = no
  tocar; ajenos al patrón = ignorar.
- **Acceptance:** checklist de `rotacion` (5 backups + keep_last=3 → quedan 3).

### T4: `guardian restore` — story `restore` (depends_on: verify)

- Reconstrucción verificada contra manifiesto; protección `--overwrite`.
- **Acceptance:** checklist de `restore` (diff -r sin diferencias).

### T5: `guardian status --json` — story `status-report` (depends_on: checker-core)

- Reporte de estado de backups, humano y JSON; pure read. **Ejecución
  MCP-first**: interacción con el tracker solo vía `arggon mcp` (JSON-RPC
  stdio), documentando límites de MCP.
- **Acceptance:** checklist de `status-report` (+ nota de documentación MCP).

## Orden de ejecución

```text
T1 (checker-core) ──► T2 (verify) ──► T3 (rotacion)
                        │    └────────► T4 (restore)
                        └────────► (T2 y T5 paralelizables tras T1)
T5 (status-report, MCP-first)
```

T2/T5 paralelizables (ambas solo dependen de T1); T3/T4 paralelizables entre sí
tras T2. Cada story = un branch/PR que referencia el id; el spec y este plan se
marcan `implemented` en el PR de la última story que aterriza.

## Estado de implementación (2026-09-13)

- T1 checker-core ✅ (PR #7) · T2 verify ✅ (PR #10) · T5 status-report ✅ (PR #9,
  MCP-first) · T3 rotacion ✅ (PR #11).
- T4 restore ✅ (PR de cierre): robada vía `--steal` por **arggonhuman**
  (2026-09-13, tras el test de caos) e implementada por el agente coordinador
  por encargo del humano. Con T4 aterrizado, spec y plan pasan a `implemented`.
