---
playbook_id: pytest
version: 9.1.1
researched: 2026-09-13
status: current
---

# pytest playbook

Technology playbook: **pytest 9.1.1**, framework de tests de guardian.

## Setup

- Instalado como dependency-group de dev (`[dependency-groups] dev` con
  `pytest>=8.3`): `uv sync --dev` lo trae; verificar con `uv run pytest --version`
  → `pytest 9.1.1` (verificado en este repo, 2026-09-13).
- Fuente: [changelog oficial de pytest](https://docs.pytest.org/en/stable/changelog.html)
  (consultado 2026-09-13): 9.1.1 publicada **2026-06-19** (fixes sobre 9.1.0 del
  2026-06-13: bug de lógica en `pytest.RaisesGroup` y regresión de 9.1.0).

## Conventions

- Config en `pyproject.toml` bajo `[tool.pytest.ini_options]`: `testpaths =
  ["tests"]` — pytest 9 soporta config nativa en TOML/pyproject
  ([release 9.0.0](https://docs.pytest.org/en/stable/announce/release-9.0.0.html),
  consultado 2026-09-13).
- Un archivo de tests por módulo de producción (`test_config.py`,
  `test_copier.py`, `test_backup.py`); nombres de test = comportamiento
  documentado (`test_cli_dry_run_does_not_write`).
- Fixtures: `tmp_path` nativo para FS efímero; `monkeypatch` para forzar
  fallos de hash. Nada de fixtures compartidos con estado global.
- Excepciones esperadas con `pytest.raises(..., match=...)` anclando el mensaje.

## Testing

- Correr: `uv run pytest` (completo, es la puerta de merge — ver
  `docs/engineering.md`);suite actual: 21 tests en ~0.05 s.
- pytest 9 introdujo **subtests** nativos y modo estricto; removió deprecaciones
  de la serie 8 — no copiar patrones pre-9 de blogs viejos
  ([changelog](https://docs.pytest.org/en/stable/changelog.html), 2026-09-13).

## Security

- Mantener pytest en el patch vigente de la serie 9.1.x: los patches incluyen
  fixes de regresiones que pueden ocultar tests fallando (9.1.1 exactamente eso:
  [changelog](https://docs.pytest.org/en/stable/changelog.html), 2026-06-19).
- No ejecutar suites contra directorios de usuario sin `tmp_path`: los tests de
  guardian escriben solo bajo `tmp_path` por diseño.

## Upgrade policy

- Re-research al marcar stale (>90 días) o al saltar de serie (9.x → 10).
- Al subir laconstraint de `pyproject.toml`, actualizar este playbook en el
  mismo PR y cerrar con `arggon playbook refresh pytest --version <v>`.
