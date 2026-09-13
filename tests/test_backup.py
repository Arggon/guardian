"""Tests de la orquestación de backup y del CLI."""

import json

import pytest

import guardian.copier as guardian_copier
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


# --- checker core: resumen por origen y exit codes (issue #1) ---


@pytest.fixture()
def multi_environment(tmp_path):
    src_a = tmp_path / "origen_a"
    src_a.mkdir()
    (src_a / "a.txt").write_text("contenido a", encoding="utf-8")
    src_b = tmp_path / "origen_b"
    src_b.mkdir()
    (src_b / "b.txt").write_text("contenido b", encoding="utf-8")
    dest = tmp_path / "backups"
    dest.mkdir()
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(
        f'[[sources]]\npath = "{src_a}"\n\n[[sources]]\npath = "{src_b}"\n\n'
        f'[destination]\npath = "{dest}"\n',
        encoding="utf-8",
    )
    return cfg_file, src_a, src_b, dest


def test_multi_source_partial_run_exit_4(multi_environment, monkeypatch, capsys):
    """Un origen fallido no aborta los demás: exit 4 y el sano queda copiado."""
    cfg_file, src_a, src_b, dest = multi_environment

    real_hash_file = guardian_copier.hash_file

    def failing_hash(path):
        if str(path).startswith(str(src_b)):
            raise guardian_copier.HashMismatch(f"simulado para {path}")
        return real_hash_file(path)

    monkeypatch.setattr(guardian_copier, "hash_file", failing_hash)

    rc = main(["backup", "--config", str(cfg_file)])

    assert rc == 4
    manifest = json.loads(next(dest.glob("*/manifest.json")).read_text(encoding="utf-8"))
    by_root = {entry["root"]: entry for entry in manifest["sources"]}
    assert by_root[str(src_a)]["status"] == "ok"
    assert by_root[str(src_b)]["status"] == "failed"
    assert "error" in by_root[str(src_b)]
    copied = dest / manifest["backup_id"] / "origen_a" / "a.txt"
    assert copied.read_text(encoding="utf-8") == "contenido a"
    out = capsys.readouterr().out
    assert "OK" in out and "FAILED" in out


def test_all_sources_ok_exit_0(multi_environment):
    cfg_file, src_a, src_b, dest = multi_environment

    rc = main(["backup", "--config", str(cfg_file)])

    assert rc == 0
    manifest = json.loads(next(dest.glob("*/manifest.json")).read_text(encoding="utf-8"))
    assert [entry["status"] for entry in manifest["sources"]] == ["ok", "ok"]
    assert all("error" not in entry for entry in manifest["sources"])


def test_single_source_hash_mismatch_exit_3(environment, monkeypatch):
    """Compat v0.1: un solo origen con HashMismatch sigue terminando en exit 3."""
    cfg_file, src, dest = environment

    def failing_hash(path):
        raise guardian_copier.HashMismatch(f"corrupción simulada para {path}")

    monkeypatch.setattr(guardian_copier, "hash_file", failing_hash)

    rc = main(["backup", "--config", str(cfg_file)])

    assert rc == 3
    manifest = json.loads(next(dest.glob("*/manifest.json")).read_text(encoding="utf-8"))
    assert manifest["sources"][0]["status"] == "failed"
    assert "HashMismatch" in manifest["sources"][0]["error"]


def test_partial_manifest_marks_failed_entry(multi_environment, monkeypatch):
    cfg_file, src_a, src_b, dest = multi_environment

    real_hash_file = guardian_copier.hash_file

    def failing_hash(path):
        if str(path).startswith(str(src_b)):
            raise OSError(f"permiso denegado leyendo {path}")
        return real_hash_file(path)

    monkeypatch.setattr(guardian_copier, "hash_file", failing_hash)

    result = run_backup(load_config(cfg_file))

    assert result.exit_code == 4
    failed = [s for s in result.sources if s.status == "failed"]
    assert len(failed) == 1
    assert failed[0].root == src_b
    assert failed[0].error is not None and failed[0].error.startswith("OSError:")
    manifest = read_manifest(result.backup_dir)
    failed_entry = next(e for e in manifest["sources"] if e["status"] == "failed")
    assert failed_entry["root"] == str(src_b)
    assert failed_entry["error"].startswith("OSError:")


def test_dry_run_with_failure_writes_nothing(multi_environment, monkeypatch):
    """El dry-run sigue sin escribir nada, incluso con orígenes fallidos."""
    cfg_file, src_a, src_b, dest = multi_environment

    real_hash_file = guardian_copier.hash_file

    def failing_hash(path):
        if str(path).startswith(str(src_b)):
            raise guardian_copier.HashMismatch("simulado")
        return real_hash_file(path)

    monkeypatch.setattr(guardian_copier, "hash_file", failing_hash)

    result = run_backup(load_config(cfg_file), dry_run=True)

    assert list(dest.iterdir()) == []
    statuses = {s.status for s in result.sources}
    assert statuses == {"ok", "failed"}


def test_cli_help_documents_exit_codes(capsys):
    """La tabla de exit codes está en el epílogo del help del subcomando backup."""
    with pytest.raises(SystemExit) as excinfo:
        main(["backup", "--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for code in ("0", "2", "3", "4"):
        assert code in out
    assert "corrida parcial" in out
