# guardian

Automatizador de backups personales: respalda carpetas locales con **verificación
de integridad SHA-256**, rotación por antigüedad y (a futuro) notificaciones.

## Stack

- **Python 3.13** (gestionado con [uv](https://docs.astral.sh/uv/)), solo stdlib en runtime
  (`shutil`, `tomllib`, `argparse`, `hashlib`).
- **pytest** para tests, **ruff** para lint/format.
- Sin framework web ni dependencias de runtime: una herramienta de CLI que tiene que
  funcionar el día que la necesitás.

## Motivación

Los backups personales suelen fallar en silencio: la copia se corre, el disco se llena,
un archivo se copia corrupto y nadie se entera hasta que hay que restaurar. `guardian`
ataca ese problema por diseño:

1. **Cada archivo se verifica** — se hashea el origen y la copia recién hecha con
   SHA-256; si no coinciden, la copia se descarta y el backup falla ruidosamente.
2. **Cada backup es inmutable y autocontenido** — una corrida escribe a
   `<destino>/<YYYYMMDD-HHMMSS>/` con un `manifest.json`; nunca pisa backups previos.
3. **El manifiesto es la verdad** — restaurar o auditar es leer JSON plano, no un
   formato propietario (ver [docs/FORMAT.md](docs/FORMAT.md)).

## Uso

```bash
uv sync                          # crea .venv e instala el proyecto
uv run guardian backup --config guardian.toml --dry-run   # plan sin escribir nada
uv run guardian backup --config guardian.toml             # backup real
```

Configuración de ejemplo ([guardian.example.toml](guardian.example.toml)):

```toml
[[sources]]
path = "/home/arggon/Documents"

[destination]
path = "/mnt/backup/guardian"
keep_last = 5
```

## Desarrollo

```bash
uv sync --dev            # dependencias de dev (pytest, ruff)
uv run pytest            # suite de tests
uv run ruff check .      # lint
uv run ruff format .     # formato
```

## Estado y plan

- [x] Esqueleto: config TOML, motor de copia con verificación, CLI `backup --dry-run`
- [ ] Verificación independiente (`guardian verify`) — issue #2
- [ ] Rotación `keep-last-N` — issue #3
- [ ] Restore — issue #4
- [ ] Reporte por Telegram — issue #5

Decisiones de diseño en [docs/DECISIONS.md](docs/DECISIONS.md).
