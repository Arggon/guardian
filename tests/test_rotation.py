"""Tests de `guardian rotate`: keep-last-N sobre backups completos."""

import json
import time

from guardian.backup import run_backup
from guardian.cli import main
from guardian.config import load_config

EPOCH = time.mktime((2026, 9, 13, 12, 0, 0, 0, 0, -1))


def _make_config(tmp_path, keep_last=None):
    src = tmp_path / "documentos"
    src.mkdir()
    (src / "nota.txt").write_text("hola guardian", encoding="utf-8")
    dest = tmp_path / "backups"
    dest.mkdir()
    dest_table = f'[destination]\npath = "{dest}"\n'
    if keep_last is not None:
        dest_table += f"keep_last = {keep_last}\n"
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(f'[[sources]]\npath = "{src}"\n\n{dest_table}', encoding="utf-8")
    return cfg_file, dest


def _write_manifest(backup_dir):
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "datos").mkdir(exist_ok=True)
    (backup_dir / "datos" / "a.txt").write_text("x", encoding="utf-8")
    manifest = {
        "guardian_version": "0.2.0",
        "created_at": "2026-09-13T12:00:00+0000",
        "backup_id": backup_dir.name,
        "dry_run": False,
        "sources": [{"root": "/tmp/x", "status": "ok", "files": []}],
    }
    (backup_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _fake_backups(dest, ids):
    for backup_id in ids:
        _write_manifest(dest / backup_id)


def test_rotate_keeps_newest_three_of_five(tmp_path):
    cfg_file, dest = _make_config(tmp_path, keep_last=3)
    _fake_backups(dest, ["20260913-010000", "20260913-020000", "20260913-030000",
                         "20260913-040000", "20260913-050000"])
    assert main(["rotate", "--config", str(cfg_file)]) == 0
    remaining = sorted(p.name for p in dest.iterdir())
    assert remaining == ["20260913-030000", "20260913-040000", "20260913-050000"]


def test_rotate_with_run_backup_timestamps(tmp_path):
    """Backups reales (run_backup con now) rotan igual que los falsos."""
    cfg_file, dest = _make_config(tmp_path, keep_last=2)
    cfg = load_config(cfg_file)
    for offset in range(5):
        run_backup(cfg, now=EPOCH - offset * 3600)
    assert main(["rotate", "--config", str(cfg_file)]) == 0
    remaining = sorted(p.name for p in dest.iterdir())
    assert len(remaining) == 2
    assert remaining == ["20260913-110000", "20260913-120000"]


def test_rotate_never_deletes_dir_without_manifest(tmp_path, capsys):
    cfg_file, dest = _make_config(tmp_path, keep_last=1)
    _fake_backups(dest, ["20260913-010000", "20260913-020000"])
    # corrida en curso: patrón timestamp pero sin manifiesto
    in_progress = dest / "20260913-030000"
    (in_progress / "datos").mkdir(parents=True)
    assert main(["rotate", "--config", str(cfg_file)]) == 0
    assert in_progress.is_dir()  # nunca se borra
    # el más viejo con manifiesto SÍ se borró (keep=1)
    assert not (dest / "20260913-010000").exists()
    out = capsys.readouterr().out
    assert "SKIP" in out and "20260913-030000" in out
    assert "20260913-020000" in out  # queda reportado entre los que quedan


def test_rotate_skipped_dir_does_not_count_for_keep(tmp_path):
    cfg_file, dest = _make_config(tmp_path, keep_last=2)
    _fake_backups(dest, ["20260913-010000", "20260913-020000", "20260913-030000"])
    # sin manifiesto: skipped, no cuenta para keep_last => no libera cupo
    (dest / "20260913-040000").mkdir()
    assert main(["rotate", "--config", str(cfg_file)]) == 0
    assert not (dest / "20260913-010000").exists()
    assert (dest / "20260913-020000").is_dir()
    assert (dest / "20260913-030000").is_dir()
    assert (dest / "20260913-040000").is_dir()


def test_rotate_ignores_dirs_without_timestamp_pattern(tmp_path, capsys):
    cfg_file, dest = _make_config(tmp_path, keep_last=1)
    _fake_backups(dest, ["20260913-010000", "20260913-020000"])
    (dest / "backup").mkdir()  # p. ej. backup/ de arggon
    (dest / ".git").mkdir()
    (dest / "notas.txt").write_text("no es un dir de backup", encoding="utf-8")
    assert main(["rotate", "--config", str(cfg_file)]) == 0
    assert (dest / "backup").is_dir()
    assert (dest / ".git").is_dir()
    assert (dest / "notas.txt").is_file()
    out = capsys.readouterr().out
    # ignorados en silencio: no aparecen como BORRADO ni SKIP
    assert "BORRADO   backup" not in out and "SKIP      backup" not in out


def test_rotate_keep_flag_overrides_config(tmp_path):
    cfg_file, dest = _make_config(tmp_path, keep_last=3)
    _fake_backups(dest, ["20260913-010000", "20260913-020000", "20260913-030000",
                         "20260913-040000", "20260913-050000"])
    assert main(["rotate", "--config", str(cfg_file), "--keep", "4"]) == 0
    remaining = sorted(p.name for p in dest.iterdir())
    assert remaining == ["20260913-020000", "20260913-030000", "20260913-040000",
                         "20260913-050000"]


def test_rotate_keep_zero_is_config_error(tmp_path, capsys):
    cfg_file, dest = _make_config(tmp_path, keep_last=3)
    _fake_backups(dest, ["20260913-010000"])
    assert main(["rotate", "--config", str(cfg_file), "--keep", "0"]) == 2
    assert (dest / "20260913-010000").is_dir()  # nada se borró
    assert "error de configuración" in capsys.readouterr().err


def test_rotate_keep_last_zero_in_config_is_config_error(tmp_path):
    cfg_file, dest = _make_config(tmp_path, keep_last=0)
    _fake_backups(dest, ["20260913-010000"])
    assert main(["rotate", "--config", str(cfg_file)]) == 2
    assert (dest / "20260913-010000").is_dir()


def test_rotate_empty_destination_ok(tmp_path, capsys):
    cfg_file, dest = _make_config(tmp_path, keep_last=3)
    assert main(["rotate", "--config", str(cfg_file)]) == 0
    assert "quedan 0" in capsys.readouterr().out


def test_rotate_corrupt_manifest_is_skipped_not_deleted(tmp_path, capsys):
    cfg_file, dest = _make_config(tmp_path, keep_last=1)
    _fake_backups(dest, ["20260913-020000"])
    corrupt = dest / "20260913-010000"
    corrupt.mkdir()
    (corrupt / "manifest.json").write_text("{no es json", encoding="utf-8")
    # keep=1: el único elegible es 020000, así que nada se borra
    assert main(["rotate", "--config", str(cfg_file)]) == 0
    assert corrupt.is_dir()
    assert "SKIP" in capsys.readouterr().out
