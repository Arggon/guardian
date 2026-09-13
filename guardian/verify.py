"""Verificación de integridad: recomputa SHA-256 de cada archivo contra el manifiesto.

Pure read estricto: ``verify`` nunca crea, modifica ni borra nada en el
destino (docs/specs/spec-backup-pipeline-v2-001.md, invariante de pure read).
La única puerta de lectura del manifiesto sigue siendo
``backup.read_manifest()``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .backup import manifest_path, read_manifest
from .config import Config
from .copier import hash_file

TIMESTAMP_PATTERN = re.compile(r"^\d{8}-\d{6}$")


class BackupNotFoundError(RuntimeError):
    """El backup pedido no existe o no hay ninguno completo para ``latest``."""


@dataclass(frozen=True)
class FileVerdict:
    """Resultado de verificar un archivo del manifiesto contra el disco."""

    source: str  # ruta relativa a la carpeta origen (la reportamos al usuario)
    destination: str  # ruta relativa al directorio del backup
    status: str  # "ok" | "hash-mismatch" | "missing"
    expected_sha256: str
    actual_sha256: str | None = None  # None si el archivo falta


@dataclass(frozen=True)
class VerifyResult:
    backup_dir: Path
    verdicts: tuple[FileVerdict, ...]

    @property
    def ok_count(self) -> int:
        return sum(1 for v in self.verdicts if v.status == "ok")

    @property
    def mismatches(self) -> tuple[FileVerdict, ...]:
        return tuple(v for v in self.verdicts if v.status == "hash-mismatch")

    @property
    def missing(self) -> tuple[FileVerdict, ...]:
        return tuple(v for v in self.verdicts if v.status == "missing")

    @property
    def exit_code(self) -> int:
        """0 todo coincide · 3 cualquier hash-mismatch o faltante."""
        return 0 if not self.mismatches and not self.missing else 3


def is_complete(backup_dir: Path) -> bool:
    """Un backup es completo si tiene ``manifest.json`` (docs/FORMAT.md invariante 1)."""
    return manifest_path(backup_dir).is_file()


def resolve_backup(config: Config, backup_id: str) -> Path:
    """Resuelve ``<id>`` o ``latest`` a un directorio de backup **completo**.

    ``latest`` elige el timestamp más alto que tenga ``manifest.json``: los
    directorios incompletos se ignoran. Sin candidatos completos (o destino
    inexistente) lanza ``BackupNotFoundError``.
    """
    root = config.destination.path
    if backup_id == "latest":
        candidates = sorted(
            d for d in _iter_backup_dirs(root) if TIMESTAMP_PATTERN.match(d.name) and is_complete(d)
        )
        if not candidates:
            raise BackupNotFoundError(f"no hay backups completos (con manifest.json) en {root}")
        return candidates[-1]
    backup_dir = root / backup_id
    if not TIMESTAMP_PATTERN.match(backup_id) or not backup_dir.is_dir():
        raise BackupNotFoundError(f"no existe el backup: {backup_dir}")
    return backup_dir


def _iter_backup_dirs(root: Path):
    if not root.is_dir():
        return
    yield from (p for p in root.iterdir() if p.is_dir())


def verify_backup(backup_dir: Path) -> VerifyResult:
    """Verifica cada archivo del manifiesto contra la copia en disco.

    Lanza ``ManifestError`` (de ``backup``) si el manifiesto falta o es
    inválido — el backup es incompleto y no verificable. Nunca escribe.
    """
    manifest = read_manifest(backup_dir)
    verdicts: list[FileVerdict] = []
    for source in manifest["sources"]:
        for entry in source.get("files", []):
            destination = entry["destination"]
            path = backup_dir / destination
            expected = entry["sha256"]
            if not path.is_file():
                verdicts.append(
                    FileVerdict(
                        source=entry["path"],
                        destination=destination,
                        status="missing",
                        expected_sha256=expected,
                    )
                )
                continue
            actual = hash_file(path)
            status = "ok" if actual == expected else "hash-mismatch"
            verdicts.append(
                FileVerdict(
                    source=entry["path"],
                    destination=destination,
                    status=status,
                    expected_sha256=expected,
                    actual_sha256=actual,
                )
            )
    return VerifyResult(backup_dir=backup_dir, verdicts=tuple(verdicts))


def run_verify(config: Config, backup_id: str = "latest") -> tuple[Path, VerifyResult]:
    """Resuelve el backup y lo verifica. Devuelve ``(backup_dir, resultado)``."""
    backup_dir = resolve_backup(config, backup_id)
    return backup_dir, verify_backup(backup_dir)


__all__ = [
    "BackupNotFoundError",
    "FileVerdict",
    "VerifyResult",
    "is_complete",
    "resolve_backup",
    "run_verify",
    "verify_backup",
]
