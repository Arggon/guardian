"""Tests de la orquestación de backup y del CLI."""

import json

import pytest

from guardian.backup import ManifestError, backup_timestamp, read_manifest, run_backup
from guardian.cli import main
from guardian.config import load_config


@pytest.fixture()
def environment(tmp_path):
    src = tmp_path / "documentos"
    src.mkdir()
    (src / "nota.txt").write_text("hola guardian", encoding="utf-8")
    dest = tmp_path / "backups"
    dest.mkdir()
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(
        f'[[sources]]\npath = "{src}"\n\n[destination]\npath = "{dest}"\n',
        encoding="utf-8",
    )
    return cfg_file, src, dest


def test_backup_timestamp_format():
    assert backup_timestamp(1789347600.0).count("-") == 1
    stamp = backup_timestamp(1789347600.0)
    date, clock = stamp.split("-")
    assert len(date) == 8 and date.isdigit()
    assert len(clock) == 6 and clock.isdigit()


def test_run_backup_copies_hashes_and_manifest(environment):
    cfg_file, src, dest = environment
    cfg = load_config(cfg_file)

    result = run_backup(cfg, now=1789347600.0)

    backup_dir = dest / "20260912-134000"  # hora local puede variar: no la fijamos
    assert result.backup_dir.parent == dest
    backup_dir = result.backup_dir
    copied = backup_dir / "documentos" / "nota.txt"
    assert copied.read_text(encoding="utf-8") == "hola guardian"

    manifest = read_manifest(backup_dir)
    assert manifest["backup_id"] == backup_dir.name
    assert manifest["dry_run"] is False
    entry = manifest["sources"][0]["files"][0]
    assert entry["path"] == "nota.txt"
    assert entry["size"] == len("hola guardian")
    assert len(entry["sha256"]) == 64


def test_run_backup_dry_run_writes_nothing(environment):
    cfg_file, src, dest = environment
    cfg = load_config(cfg_file)

    result = run_backup(cfg, dry_run=True)

    assert list(dest.iterdir()) == []
    assert result.records[0].source == "nota.txt"


def test_read_manifest_missing(tmp_path):
    with pytest.raises(ManifestError, match="no existe"):
        read_manifest(tmp_path)


def test_read_manifest_corrupt(tmp_path):
    (tmp_path / "manifest.json").write_text("{nope", encoding="utf-8")
    with pytest.raises(ManifestError, match="corrupto"):
        read_manifest(tmp_path)


def test_cli_backup_end_to_end(environment, capsys):
    cfg_file, src, dest = environment

    rc = main(["backup", "--config", str(cfg_file)])

    assert rc == 0
    out = capsys.readouterr().out
    assert "BACKUP" in out
    manifest = json.loads(next(dest.glob("*/manifest.json")).read_text(encoding="utf-8"))
    assert manifest["sources"][0]["files"][0]["path"] == "nota.txt"


def test_cli_dry_run_does_not_write(environment, capsys):
    cfg_file, src, dest = environment

    rc = main(["backup", "--config", str(cfg_file), "--dry-run"])

    assert rc == 0
    assert list(dest.iterdir()) == []
    assert "PLAN" in capsys.readouterr().out


def test_cli_config_error_exit_code(tmp_path, capsys):
    rc = main(["backup", "--config", str(tmp_path / "missing.toml")])
    assert rc == 2
    assert "error de configuración" in capsys.readouterr().err
