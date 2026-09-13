"""CLI de guardian: ``guardian backup [--dry-run]``, ``guardian status``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .backup import run_backup
from .config import ConfigError, load_config
from .status import collect_status

DEFAULT_CONFIG = Path("guardian.toml")

BACKUP_EPILOG = """\
exit codes de `guardian backup`:
  0  todos los orígenes fueron copiados y verificados (ok)
  2  error de configuración (TOML ausente, inválido o fuentes inexistentes)
  3  falla de integridad total: todos los orígenes fallaron con HashMismatch
     (v0.1: un solo origen con hash mismatch mantiene este comportamiento)
  4  corrida parcial: al menos un origen ok y al menos uno fallido
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="guardian",
        description="Backups personales con verificación de integridad SHA-256.",
    )
    parser.add_argument("--version", action="version", version=f"guardian {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    backup = sub.add_parser(
        "backup",
        help="ejecuta un backup de las carpetas configuradas",
        epilog=BACKUP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    backup.add_argument("--config", "-c", type=Path, default=DEFAULT_CONFIG, help="ruta del TOML")
    backup.add_argument(
        "--dry-run",
        action="store_true",
        help="muestra el plan (archivos y hashes) sin escribir nada en disco",
    )

    status = sub.add_parser(
        "status",
        help="lista los backups del destino (lectura pura)",
    )
    status.add_argument("--config", "-c", type=Path, default=DEFAULT_CONFIG, help="ruta del TOML")
    status.add_argument("--json", action="store_true", help="salida JSON en stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "status":
        try:
            config = load_config(args.config)
        except ConfigError as exc:
            print(f"error de configuración: {exc}", file=sys.stderr)
            return 2
        backups = collect_status(config.destination.path)
        if args.json:
            payload = {
                "backups": [
                    {
                        "id": b.id,
                        "created_at": b.created_at,
                        "files": b.files,
                        "bytes": b.bytes,
                        "complete": b.complete,
                    }
                    for b in backups
                ]
            }
            print(json.dumps(payload, indent=2))
            return 0
        if not backups:
            print(f"sin backups en {config.destination.path}")
            return 0
        print(f"backups en {config.destination.path}: {len(backups)}")
        for b in backups:
            mark = "ok" if b.complete else "incompleto"
            created = b.created_at if b.created_at else "—"
            print(f"  {b.id}  {created}  {b.files} archivo(s)  {b.bytes} B  [{mark}]")
        return 0

    if args.command == "backup":
        try:
            config = load_config(args.config)
            result = run_backup(config, dry_run=args.dry_run)
        except ConfigError as exc:
            print(f"error de configuración: {exc}", file=sys.stderr)
            return 2

        mode = "PLAN (dry-run, nada escrito)" if result.dry_run else "BACKUP"
        print(f"guardian {mode} -> {result.backup_dir}")
        for report in result.sources:
            if report.status == "ok":
                print(f"  OK     {report.root} ({len(report.records)} archivo(s))")
            else:
                print(f"  FAILED {report.root} — {report.error}")
        for record in result.records:
            print(f"  {record.source}  ({record.size} B, sha256 {record.sha256[:12]}…)")
        print(f"{len(result.records)} archivo(s) verificado(s) con SHA-256")
        return 0 if result.dry_run else result.exit_code

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
