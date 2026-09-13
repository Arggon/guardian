---
playbook_id: uv
version: 0.12.13
researched: 2026-09-13
status: current
---

# uv playbook

Technology playbook: [uv](https://docs.astral.sh/uv/) (Astral) **0.12.13**,
gestor de proyectos/entornos Python de guardian.

## Setup

- Instalación standalone: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  (binario en `~/.local/bin/uv`). Verificado en esta máquina el 2026-09-13:
  `uv 0.12.13`.
- Fuente: [astral-sh/uv releases](https://github.com/astral-sh/uv/releases)
  (consultado 2026-09-13): 0.12.13 publicada 2026-09-10; highlights de la semana —
  soporte de verificación por hash y wheels de `uv`/`uv_build` **code-signed**
  (2026-09-09).

## Conventions

- **Comandos del repo** (nunca pip directo): `uv sync --dev` para instalar todo
  (crea `.venv`), `uv run <cmd>` para ejecutar dentro del entorno (`uv run
  pytest`, `uv run guardian`). `uv.lock` se commitea — es una app, no una lib.
- El proyecto se instala editable en el venv porque `pyproject.toml` declara
  `[build-system]` (hatchling); sin ese bloque uv trata el proyecto como virtual
  y `uv run guardian` no encuentra el entry point (paso por eso el 2026-09-13).
- Python también lo gestiona uv vía `.python-version` (`3.13`) — ver
  `python.md`.
- Dependencias de dev van en `[dependency-groups] dev` (PEP 735), no en
  `project.dependencies` (que permanece vacío por decisión — `docs/DECISIONS.md` §4).

## Testing

- El propio `uv run pytest` es el runner estándar; no hay pasos post-sync: un
  `uv sync --dev` fresco deja el repo listo para testear.
- En worktrees (ArggonManager): correr `uv sync` al entrar — configurado como
  `x-worktree.post-start` en `tasks/.convention.yml`.

## Security

- Mantener uv actualizado (patch mensual aprox.); los releases de septiembre
  2026 firmaron los wheels — verificar firma al instalar en CI
  ([releases](https://github.com/astral-sh/uv/releases), 2026-09-10).
- El lockfile (`uv.lock`) fija hashes de distribución: no regenerar a mano;
  `uv lock --upgrade` en un PR dedicado cuando toque.

## Upgrade policy

- Re-research al marcar stale (>90 días, `arggon playbook status`) o ante un
  minor nuevo de uv con cambios que afecten el flujo (lock, groups, worktrees).
- Actualizar: versión en Setup, changelog relevante con fecha, y luego
  `arggon playbook refresh uv --version <v>`.
