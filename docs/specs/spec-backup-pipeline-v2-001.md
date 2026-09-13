---
spec_id: backup-pipeline-v2-001
title: Pipeline de backup v0.2: checker core, verify, rotación, restore y status
status: implemented
created: 2026-09-13
---

# Spec: Pipeline de backup v0.2 (backup-pipeline-v2-001)

## Purpose

El esqueleto v0.1 copia y verifica pero no se puede operar: no hay forma de
supervisar una corrida (¿falló algo? ¿cuánto copió?), verificar un backup viejo
contra su manifiesto, limitar el espacio (rotación) ni restaurar. Esta spec
define el pipeline v0.2 alrededor del motor existente.

**Invariants** (heredan de `ARCHITECTURE.md` y `docs/FORMAT.md`):

- Un dry-run nunca escribe nada en disco.
- Una copia cuyo SHA-256 no coincide con el origen se descarta y falla ruidosamente.
- Ninguna operación (backup, rotación, restore) **pisa o muta** un backup anterior
  con `manifest.json` válido; la rotación solo borra backups completos más viejos
  que `keep_last`.
- Un backup sin `manifest.json` es incompleto: no es verificable, no es
  restaurable vía manifiesto y no es candidato a borrado por rotación.
- `guardian verify` y `guardian status` son **pure reads** del destino: nunca
  escriben.

## Synopsis

```bash
guardian backup  [--config guardian.toml] [--dry-run]   # v0.1 + resumen por origen y exit codes
guardian verify  [--backup <id|latest>] [--config guardian.toml]
guardian rotate  [--config guardian.toml] [--keep N]    # keep_last de config por defecto
guardian restore <backup_id|latest> --dest <ruta> [--overwrite]
guardian status  [--config guardian.toml]               # reporte de estado de backups
```

Exit codes transversales: 0 ok · 2 config · 3 integridad · 4 backup parcial.
JSON de `status`/`verify` a stdout con `--json` (para el reporte por Telegram).

- `backup` (checker core, issue #1): resumen por origen (ok/parcial/fallida,
  archivos, bytes, errores) y exit 4 si algún origen falló sin abortar los demás.
- `verify` (issue #2): recomputa SHA-256 de cada archivo del backup contra su
  `manifest.json`; reporta ok / hash-mismatch / faltante; backup sin manifiesto
  = incompleto (error, no crash).
- `rotate` (issue #3): ordena directorios `YYYYMMDD-HHMMSS` con manifiesto
  válido, borra los más viejos dejando `keep_last`; ignora directorios sin
  manifiesto y ajenos al patrón.
- `restore` (issue #4): reconstruye los orígenes desde un backup verificado,
  re-verificando hashes; exige `--overwrite` si el destino existe no vacío.
- `status` (issue #5-adjacente, reporte local de estado): lista backups
  existentes con fecha, cantidad de archivos, bytes, y resultado del último
  verify conocido; `--json` para automatizar.

## Acceptance

- [x] `guardian backup` con un origen fallido (permiso denegado simulado) termina
      con exit 4, reporta el origen fallido y los orígenes sanos quedan copiados.
- [x] `guardian verify` detecta un byte corrupto (hash mismatch) con exit 3 y
      reporta el archivo exacto; con manifiesto ausente reporta "incompleto".
- [x] `guardian rotate` con keep_last=3 y 5 backups completos deja exactamente
      los 3 más nuevos; un directorio sin manifiesto NO es borrado.
- [x] `guardian restore` de un backup a destino limpio reproduce el árbol con
      `diff -r` sin diferencias; sin `--overwrite` sobre destino no vacío falla
      con exit 2.
- [x] `guardian status --json` emite un array de backups con id, fecha, archivos,
      bytes y estado; nunca escribe en el destino.
- [x] Cada comando nueva tiene tests unitarios (tmp_path) y la suite completa
      queda verde (`uv run pytest` + `uv run ruff check .`).
