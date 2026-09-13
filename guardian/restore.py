"""Restore: reconstrucción verificada desde un backup hacia una ruta de destino.

Reconstruye cada carpeta origen bajo ``--dest`` preservando el basename del
origen (``dest/<nombre-origen>/<ruta-relativa>``), re-verificando el SHA-256 de
cada archivo contra el manifiesto **antes** de escribirlo: un archivo corrupto
nunca llega al destino. La resolución de ``<id>|latest`` y la noción de backup
completo se reutilizan de ``verify`` (dependencia declarada en el grafo).
El backup origen es pure read: restore nunca escribe en él.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .backup import read_manifest
from .config import Config
from .copier import hash_file
from .verify import resolve_backup


class RestoreError(RuntimeError):
    """El restore no puede proceder (destino problemático o backup inconsistente)."""


class RestoreHashMismatch(RestoreError):
    """Un archivo del backup no coincide con el hash del manifiesto."""


class DestNotEmptyError(RestoreError):
    """El destino existe, no está vacío y no se pasó ``--overwrite``."""


@dataclass(frozen=True)
class RestoreResult:
    backup_dir: Path
    dest: Path
    files: int
    bytes: int


def ensure_dest(dest: Path, *, overwrite: bool) -> None:
    """Valida el destino: o está vacío/inexistente, o hubo ``--overwrite``."""
    if dest.exists() and not dest.is_dir():
        raise DestNotEmptyError(f"el destino existe y no es un directorio: {dest}")
    if dest.is_dir() and any(dest.iterdir()) and not overwrite:
        raise DestNotEmptyError(
            f"el destino {dest} no está vacío; usá --overwrite para restaurar encima"
        )


def run_restore(
    config: Config, backup_ref: str, dest: Path, *, overwrite: bool = False
) -> RestoreResult:
    """Restaura el backup ``backup_ref`` (id o ``latest``) hacia ``dest``.

    Lanza ``BackupNotFoundError`` (backup inexistente), ``DestNotEmptyError``
    (destino no vacío sin ``--overwrite``), ``ManifestError`` (manifiesto
    ausente/corrupto) y ``RestoreHashMismatch``/``RestoreError`` (integridad).
    """
    dest = dest.expanduser().resolve()
    ensure_dest(dest, overwrite=overwrite)
    backup_dir = resolve_backup(config, backup_ref)
    manifest = read_manifest(backup_dir)

    files = 0
    total_bytes = 0
    for source in manifest["sources"]:
        for entry in source.get("files", []):
            src = backup_dir / entry["destination"]
            if not src.is_file():
                raise RestoreError(
                    f"archivo del manifiesto ausente en el backup: {entry['destination']}"
                )
            actual = hash_file(src)
            if actual != entry["sha256"]:
                raise RestoreHashMismatch(
                    f"hash-mismatch en el backup: {entry['destination']} "
                    f"(esperado={entry['sha256'][:12]}… obtenido={actual[:12]}…)"
                )
            target = dest / entry["destination"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            files += 1
            total_bytes += entry["size"]
    return RestoreResult(backup_dir=backup_dir, dest=dest, files=files, bytes=total_bytes)


__all__ = [
    "DestNotEmptyError",
    "RestoreError",
    "RestoreHashMismatch",
    "RestoreResult",
    "run_restore",
]
