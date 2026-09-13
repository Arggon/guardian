"""Reporte de estado de backups: lectura pura del destino.

Lista los directorios de backup (patrón ``YYYYMMDD-HHMMSS``) con id, fecha
del manifiesto, cantidad de archivos, bytes totales y completitud. Nunca
escribe en el destino (spec-backup-pipeline-v2-001).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .backup import ManifestError, read_manifest

BACKUP_ID_RE = re.compile(r"^\d{8}-\d{6}$")


@dataclass(frozen=True)
class BackupStatus:
    """Estado de un directorio de backup en el destino."""

    id: str
    created_at: str | None
    files: int
    bytes: int
    complete: bool


def list_backup_ids(dest: Path) -> list[str]:
    """Ids de backups (directorios ``YYYYMMDD-HHMMSS``), ordenados por id."""
    if not dest.is_dir():
        return []
    return sorted(p.name for p in dest.iterdir() if p.is_dir() and BACKUP_ID_RE.match(p.name))


def _measure_on_disk(backup_dir: Path) -> tuple[int, int]:
    """(archivos, bytes) contando el árbol en disco (para backups sin manifiesto)."""
    files = 0
    total = 0
    for path in backup_dir.rglob("*"):
        if path.is_file():
            files += 1
            total += path.stat().st_size
    return files, total


def backup_status(dest: Path, backup_id: str) -> BackupStatus:
    """Estado de un backup: manifiesto presente y parseable => complete."""
    backup_dir = dest / backup_id
    try:
        manifest = read_manifest(backup_dir)
    except ManifestError:
        files, total = _measure_on_disk(backup_dir)
        return BackupStatus(backup_id, None, files, total, complete=False)
    files = 0
    total = 0
    for source in manifest.get("sources", []):
        for record in source.get("files", []):
            files += 1
            total += int(record.get("size", 0))
    created_at = manifest.get("created_at")
    return BackupStatus(
        backup_id,
        created_at if isinstance(created_at, str) else None,
        files,
        total,
        complete=True,
    )


def collect_status(dest: Path) -> list[BackupStatus]:
    """Estado de todos los backups del destino (lista vacía si no hay)."""
    return [backup_status(dest, backup_id) for backup_id in list_backup_ids(dest)]
