---
playbook_id: python
version: 3.13.15
researched: 2026-09-13
status: current
---

# Python playbook

Technology playbook: Python 3.13 (patch vigente **3.13.15**), la base runtime de
guardian. Toda sección cita fuentes fechadas para poder re-verificar.

## Setup

- Python se gestiona **con uv, no con el intérprete del sistema**: el archivo
  `.python-version` (contenido: `3.13`) fija la serie y uv descarga el patch
  vigente la primera vez que hace `uv sync`.
- Verificación local (2026-09-13): `uv run python --version` → `Python 3.13.15`.
- `pyproject.toml` declara `requires-python = ">=3.13"`; no usar sintaxis de
  3.14+ (el piso es 3.13).
- Fuente: python.org — [Versions](https://www.python.org/doc/versions/) (consultado
  2026-09-13): 3.13.15 publicada el 2026-08-05, patch vigente de la serie 3.13.

## Conventions

- **Solo stdlib en runtime** (`shutil`, `tomllib`, `hashlib`, `argparse`) — decisión
  registrada en `docs/DECISIONS.md` §4. Dependencias nuevas requieren justificación
  en el PR.
- Tipado: anotaciones en todas las funciones públicas; dataclasses `frozen` para
  valores de dominio (`Config`, `FileRecord`, `BackupResult`).
- Errores: excepciones de dominio por módulo (`ConfigError`, `HashMismatch`,
  `ManifestError`) que el CLI mapea a exit codes; nunca `sys.exit` desde el medio
  de un módulo.
- `from __future__ import annotations` al tope de cada módulo; imports ordenados
  por ruff (`I` rules).
- Estado del lenguaje 3.13: la serie entra en **fase security-only en octubre
  2026** según el cronograma de releases (fuente: python.org/devpeps/pep-0713 y
  página de versions, consultado 2026-09-13) — planificar la migración a 3.14
  durante la vida de este proyecto.

## Testing

- **pytest 9.1.1** (ver `pytest.md`); tests unitarios por módulo en `tests/`,
  filesystem efímero con el fixture `tmp_path` — ningún test toca el FS real ni red.
- Correr con `uv run pytest`; la puerta de merge es `uv run pytest` +
  `uv run ruff check .` (ver `docs/engineering.md`).

## Security

- Mantenerse en el último patch de la serie (hoy 3.13.15, 2026-08-05) — los
  patches de Python incluyen fixes de seguridad; fuente:
  [python.org/doc/versions](https://www.python.org/doc/versions/) (2026-09-13).
- El SHA-256 de guardian asume hashes no-adversariales; no hay criptografía
  propia — no introducirla sin un ADR.

## Upgrade policy

- Re-research cuando `arggon playbook status` marque este archivo como stale
  (>90 días) o cuando la serie 3.13 reciba patch.
- Migración de serie (3.13 → 3.14): ADR + actualización de `.python-version` y
  `requires-python` en el mismo PR. Tras re-research:
  `arggon playbook refresh python --version <v>`.
