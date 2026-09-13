"""Orquestación de un backup: timestamp, copia verificada y manifiesto."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .config import Config
from .copier import FileRecord, copy_tree


class ManifestError(RuntimeError):
    """El manifiesto del backup es inválido o está incompleto."""


@dataclass(frozen=True)
class SourceReport:
    root: Path
    records: tuple[FileRecord, ...]


@dataclass(frozen=True)
class BackupResult:
    backup_dir: Path
    dry_run: bool
    sources: tuple[SourceReport, ...]

    @property
    def records(self) -> tuple[FileRecord, ...]:
        return tuple(r for report in self.sources for r in report.records)


def backup_timestamp(now: float | None = None) -> str:
    """Nombre de directorio para una corrida: ``YYYYMMDD-HHMMSS`` (hora local)."""
    return time.strftime("%Y%m%d-%H%M%S", time.localtime(now if now is not None else time.time()))


def manifest_path(backup_dir: Path) -> Path:
    return backup_dir / "manifest.json"


def read_manifest(backup_dir: Path) -> dict:
    """Lee y valida mínimamente el manifiesto de un backup."""
    path = manifest_path(backup_dir)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"no existe el manifiesto: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifiesto corrupto (JSON inválido): {path}") from exc
    for key in ("guardian_version", "created_at", "backup_id", "sources"):
        if key not in manifest:
            raise ManifestError(f"al manifiesto le falta el campo '{key}': {path}")
    return manifest


def build_manifest(
    backup_dir: Path, config: Config, sources: list[SourceReport], *, dry_run: bool
) -> dict:
    """Manifiesto con el formato de docs/FORMAT.md."""
    return {
        "guardian_version": __version__,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
        "backup_id": backup_dir.name,
        "dry_run": dry_run,
        "sources": [
            {
                "root": str(report.root),
                "files": [
                    {
                        "path": r.source,
                        "destination": r.destination,
                        "size": r.size,
                        "sha256": r.sha256,
                    }
                    for r in report.records
                ],
            }
            for report in sources
        ],
    }


def run_backup(config: Config, *, dry_run: bool = False, now: float | None = None) -> BackupResult:
    """Ejecuta un backup completo: copia verificada + manifiesto.

    Cada corrida crea ``<destination>/<YYYYMMDD-HHMMSS>/`` con un
    subdirectorio por carpeta origen (nombrado con el basename del origen).
    Nunca toca backups anteriores; la rotación es responsabilidad del
    módulo de rotación.
    """
    backup_dir = config.destination.path / backup_timestamp(now)
    reports: list[SourceReport] = []
    for root in config.sources:
        target = backup_dir / root.name
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        records = copy_tree(root, target, dry_run=dry_run)
        reports.append(SourceReport(root=root, records=tuple(records)))
    if not dry_run:
        manifest = build_manifest(backup_dir, config, reports, dry_run=False)
        text = json.dumps(manifest, indent=2) + "\n"
        manifest_path(backup_dir).write_text(text, encoding="utf-8")
    return BackupResult(backup_dir=backup_dir, dry_run=dry_run, sources=tuple(reports))
