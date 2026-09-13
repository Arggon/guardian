"""Rotación keep-last-N: borra los backups completos más viejos (issue #3).

Solo considera directorios con patrón ``YYYYMMDD-HHMMSS`` cuyo manifiesto es
presente y parseable (read_manifest). Un directorio con patrón pero sin
manifiesto puede ser una corrida en curso: NUNCA se borra (skip conservador,
docs/DECISIONS.md §3). Directorios ajenos al patrón no son backups y se
ignoran siempre.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .backup import ManifestError, read_manifest
from .status import BACKUP_ID_RE, list_backup_ids


class RotationError(ValueError):
    """El keep efectivo es inválido (< 1): error de configuración."""


@dataclass(frozen=True)
class RotationResult:
    """Qué se borró, qué se skippeó y qué queda."""

    deleted: tuple[str, ...]
    skipped: tuple[tuple[str, str], ...]  # (id, motivo)
    kept: tuple[str, ...]


def eligible_ids(dest: Path) -> tuple[list[str], list[tuple[str, str]]]:
    """(ids elegibles, skips) sobre los directorios del destino.

    Elegible: patrón ``YYYYMMDD-HHMMSS`` con manifiesto presente y parseable.
    Skip: patrón con manifiesto ausente o corrupto (corrida en curso o
    incompleta). Sin patrón: ignorado en silencio (no es un backup).
    """
    eligible: list[str] = []
    skipped: list[tuple[str, str]] = []
    for backup_id in list_backup_ids(dest):
        try:
            read_manifest(dest / backup_id)
        except ManifestError as exc:
            skipped.append((backup_id, str(exc)))
            continue
        eligible.append(backup_id)
    return eligible, skipped


def run_rotation(dest: Path, keep: int) -> RotationResult:
    """Borra los backups elegibles más viejos dejando ``keep``.

    ``keep < 1`` es error de configuración (el llamante decide el exit code);
    el destino no existente o vacío es un no-op exitoso.
    """
    if keep < 1:
        raise RotationError(f"keep debe ser >= 1 (got {keep})")

    eligible, skipped = eligible_ids(dest)
    eligible.sort()  # el id ES el timestamp: orden lexicográfico = cronológico
    excess = len(eligible) - keep
    to_delete = eligible[: max(excess, 0)]

    deleted: list[str] = []
    for backup_id in to_delete:
        backup_dir = dest / backup_id
        if BACKUP_ID_RE.match(backup_id) and backup_dir.is_dir():
            shutil.rmtree(backup_dir)
            deleted.append(backup_id)

    kept = tuple(eligible[len(to_delete):])
    return RotationResult(deleted=tuple(deleted), skipped=tuple(skipped), kept=kept)
