"""CLI de guardian: ``guardian backup [--dry-run]`` y ``guardian verify``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .backup import ManifestError, run_backup
from .config import ConfigError, load_config
from .verify import BackupNotFoundError, run_verify

DEFAULT_CONFIG = Path("guardian.toml")

BACKUP_EPILOG = """\
exit codes de `guardian backup`:
  0  todos los orígenes fueron copiados y verificados (ok)
  2  error de configuración (TOML ausente, inválido o fuentes inexistentes)
  3  falla de integridad total: todos los orígenes fallaron con HashMismatch
     (v0.1: un solo origen con hash mismatch mantiene este comportamiento)
  4  corrida parcial: al menos un origen ok y al menos uno fallido
"""

VERIFY_EPILOG = """\
exit codes de `guardian verify`:
  0  todos los archivos coinciden con el manifiesto (ok)
  2  error de configuración o backup inexistente (o no hay completo para latest)
  3  falla de integridad: hash-mismatch, archivo faltante o manifiesto
     ausente/corrupto (backup incompleto)
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

    verify = sub.add_parser(
        "verify",
        help="verifica un backup contra su manifiesto (pure read)",
        epilog=VERIFY_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    verify.add_argument("--config", "-c", type=Path, default=DEFAULT_CONFIG, help="ruta del TOML")
    verify.add_argument(
        "--backup",
        "-b",
        default="latest",
        help="id del backup (YYYYMMDD-HHMMSS) o 'latest' (el más nuevo con manifiesto)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

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

    if args.command == "verify":
        try:
            config = load_config(args.config)
        except ConfigError as exc:
            print(f"error de configuración: {exc}", file=sys.stderr)
            return 2
        try:
            backup_dir, result = run_verify(config, args.backup)
        except BackupNotFoundError as exc:
            print(f"backup inexistente: {exc}", file=sys.stderr)
            return 2
        except ManifestError as exc:
            print(f"backup incompleto: {exc}", file=sys.stderr)
            return 3

        print(f"guardian VERIFY {backup_dir.name} -> {backup_dir}")
        for verdict in result.verdicts:
            if verdict.status == "ok":
                print(f"  OK            {verdict.source}")
            elif verdict.status == "missing":
                print(f"  FALTANTE      {verdict.source} (ausente en el backup)")
            else:
                print(f"  HASH-MISMATCH {verdict.source}")
                print(
                    f"                  esperado={verdict.expected_sha256[:12]}… "
                    f"obtenido={verdict.actual_sha256[:12]}…"
                )
        print(
            f"{len(result.verdicts)} archivo(s): "
            f"{result.ok_count} ok · "
            f"{len(result.mismatches)} hash-mismatch · "
            f"{len(result.missing)} faltante"
        )
        return result.exit_code

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
