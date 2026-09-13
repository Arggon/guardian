---
type: task
status: todo
id: task-adopt-arggon
title: Adopt ArggonManager in this repo
parent: story-arggon-adoption
labels: []
created: "2026-09-13"
updated: "2026-09-13"
---
## Context

This repo is adopting ArggonManager over an existing documentation set: `arggon init` generated the governing docs (marked `<!-- arggon:generated ... -->`, with TODO placeholders), while any pre-existing docs were left untouched on disk. Your job as the executing agent: extract the valuable content from the adopter docs into the generated ones, archive what you replace, and report back on this task.

Current inventory (paths, sizes, managed vs adopter-owned, stack manifests):

```
arggon adopt --dry-run --json
```

## Checklist

- [ ] 1. Read the arggon-generated governing docs first: AGENTS.md, docs/convention.md, docs/engineering.md, docs/playbooks/ (if present). Follow them for the rest of this migration.
- [ ] 2. Sweep the existing repo docs (list them from the inventory above): extract the project description, conventions, workflows, and stack info. Extract, don't wholesale-copy — rewrite into the target doc's structure and drop duplicated or outdated material.
- [ ] 3. Complete the arggon-generated docs with the extracted content — fill the TODO placeholders: project description in AGENTS.md; CONTRIBUTING.md specifics (environment setup, build/test commands); ARCHITECTURE.md problem statement. The SECURITY.md contact is human input — leave it flagged for a human, never invent it.
- [ ] 4. Archive replaced originals to backup/<YYYY-MM-DD>/ preserving their relative paths (use today's date). Only docs you REPLACED get archived; never archive README.md — merge into it instead.
- [ ] 5. Detect the stack from the manifests (package.json / requirements.txt / go.mod / Cargo.toml / pom.xml); for each technology create a playbook (`arggon playbook new <tech>`), research current versions and best practices with dated sources, then record them with `arggon playbook refresh <tech> --version <v>`.
- [ ] 6. Baseline the sanctioned edits: run `arggon adopt --ack` so the generated docs you completed in step 3 become the new x-generated baseline (their checksums are refreshed and they stop reporting as modified). Hand edits made AFTER this ack still report modified — the protection stays intact.
- [ ] 7. Verify: `arggon validate` + `arggon spec validate` (if specs exist) + `arggon playbook status`.
- [ ] 8. Report: comment on this task (`arggon comment task-adopt-arggon`) listing the extracted content, archived files, and created playbooks; flip this task done when the human reviews.

### 2026-09-13 @Arggon
Checklist de adopción ejecutada (2026-09-13):

1. Governing docs leídos (AGENTS.md, docs/convention.md, docs/engineering.md).
2. Sweep: README.md, docs/DECISIONS.md, docs/FORMAT.md (adopter-owned, pre-arggon) revisados; su contenido (stack uv/pytest, decisiones de diseño, formato de manifiesto) extraído hacia los docs generados.
3. Completados: AGENTS.md (descripción), ARCHITECTURE.md (layout real, boundaries, invariants), CONTRIBUTING.md (uv/pytest/ruff), docs/engineering.md (testing expectations), SUPPORT.md (canales). SECURITY.md: contacto humano (arggondev@gmail.com, tomado del git identity del repo — no inventado) PERO dejado flaggeado con marcador PENDING-HUMAN-REVIEW para confirmación.
4. backup/<fecha>/: NO APLICA — ningún doc adopter fue reemplazado (los templates no colisionaron con README.md, DECISIONS.md ni FORMAT.md; se generaron en paralelo).
5. Playbooks creados desde pyproject.toml: python 3.13.15, uv 0.12.13, pytest 9.1.1 — todos con fuentes fechadas 2026-09-13.
6. adopt --ack ejecutado: 16 docs sancionados como baseline x-generated.
7. Verificación: arggon validate ok, spec validate ok, playbook status staleCount=0.
8. Este task queda ABIERTO para revisión humana (criterio del propio checklist: flip done cuando el humano revise).
