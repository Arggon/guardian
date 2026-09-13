"""Motor de copia: shutil + verificación de integridad SHA-256.

Cada archivo se copia con ``shutil.copy2`` (preserva mtime/permisos) y se
hashea dos veces: el origen y la copia recién creada. Si los hashes no
coinciden, la copia se descarta y se lanza ``HashMismatch`` — guardian
prefiere fallar ruidosamente antes que reportar un backup bueno falso.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

CHUNK_SIZE = 1 << 20  # 1 MiB


def hash_file(path: Path) -> str:
    """SHA-256 en streaming de ``path``."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class FileRecord:
    """Entrada del manifiesto para un archivo copiado."""

    source: str  # ruta relativa a la carpeta origen
    destination: str  # ruta relativa al directorio del backup
    size: int
    sha256: str


class HashMismatch(RuntimeError):
    """El hash del archivo copiado no coincide con el del origen."""


def copy_file(
    source_root: Path, src: Path, backup_dir: Path, *, dry_run: bool = False
) -> FileRecord:
    """Copia ``src`` dentro de ``backup_dir`` preservando su ruta relativa.

    Verifica SHA-256(origen) == SHA-256(copia). Con ``dry_run`` no escribe
    nada: solo calcula el hash del origen y la ruta de destino planificada.
    """
    rel = src.relative_to(source_root)
    target = backup_dir / rel
    record = FileRecord(
        source=rel.as_posix(),
        destination=target.relative_to(backup_dir).as_posix(),
        size=src.stat().st_size,
        sha256=hash_file(src),
    )
    if dry_run:
        return record

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    copied_hash = hash_file(target)
    if copied_hash != record.sha256:
        target.unlink(missing_ok=True)
        raise HashMismatch(
            f"verificación fallida para {src}: origen={record.sha256[:12]} copia={copied_hash[:12]}"
        )
    return record


def iter_files(source_root: Path):
    """Recorre ``source_root`` y rinde cada archivo regular (sin symlinks)."""
    for path in sorted(source_root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            yield path


def copy_tree(source_root: Path, backup_dir: Path, *, dry_run: bool = False) -> list[FileRecord]:
    """Copia el árbol ``source_root`` dentro de ``backup_dir``.

    Devuelve los FileRecord en orden determinista. Con ``dry_run`` produce el
    plan completo sin escribir en disco.
    """
    return [
        copy_file(source_root, src, backup_dir, dry_run=dry_run) for src in iter_files(source_root)
    ]
