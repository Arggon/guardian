"""Tests de `guardian status`: reporte de estado, lectura pura del destino."""

import json

from guardian.backup import backup_timestamp, run_backup
from guardian.cli import main
from guardian.config import load_config
from guardian.status import collect_status


def _make_config(tmp_path):
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


def test_status_empty_destination(tmp_path, capsys):
    cfg_file, _src, dest = _make_config(tmp_path)
    assert collect_status(dest) == []
    assert main(["status", "--config", str(cfg_file)]) == 0
    capsys.readouterr()  # descarta la salida humana
    assert main(["status", "--config", str(cfg_file), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"backups": []}


def test_status_missing_destination(tmp_path):
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(
        f'[[sources]]\npath = "{tmp_path}"\n\n[destination]\npath = "{tmp_path / "no-existe"}"\n',
        encoding="utf-8",
    )
    config = load_config(cfg_file)
    assert collect_status(config.destination.path) == []


def test_status_lists_backup_with_manifest(tmp_path, capsys):
    cfg_file, _src, dest = _make_config(tmp_path)
    cfg = load_config(cfg_file)
    result = run_backup(cfg, now=1789347600.0)
    backup_id = backup_timestamp(1789347600.0)
    assert result.backup_dir.name == backup_id

    assert main(["status", "--config", str(cfg_file), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["backups"]) == 1
    entry = payload["backups"][0]
    assert entry["id"] == backup_id
    assert entry["complete"] is True
    assert entry["files"] == 1
    assert entry["bytes"] == len("hola guardian")
    assert isinstance(entry["created_at"], str) and entry["created_at"]

    # humano: tabla legible con marca ok
    assert main(["status", "--config", str(cfg_file)]) == 0
    out = capsys.readouterr().out
    assert backup_id in out and "ok" in out and "archivo(s)" in out


def test_status_marks_incomplete_without_manifest(tmp_path, capsys):
    cfg_file, _src, dest = _make_config(tmp_path)
    fake_id = "20250101-000000"
    fake = dest / fake_id
    fake.mkdir()
    (fake / "data.bin").write_bytes(b"x" * 10)

    assert main(["status", "--config", str(cfg_file), "--json"]) == 0
    entry = json.loads(capsys.readouterr().out)["backups"][0]
    assert entry == {
        "id": fake_id,
        "created_at": None,
        "files": 1,
        "bytes": 10,
        "complete": False,
    }

    assert main(["status", "--config", str(cfg_file)]) == 0
    assert "incompleto" in capsys.readouterr().out


def test_status_ignores_dirs_outside_pattern(tmp_path):
    cfg_file, _src, dest = _make_config(tmp_path)
    (dest / "not-a-backup").mkdir()
    (dest / "20260913.txt").write_text("no es dir")
    assert collect_status(dest) == []


def test_status_invalid_config_exit_2(tmp_path):
    assert main(["status", "--config", str(tmp_path / "missing.toml")]) == 2


def test_status_never_writes_destination(tmp_path):
    """Pure read: el árbol del destino queda byte a byte idéntico tras status."""
    import hashlib

    cfg_file, _src, dest = _make_config(tmp_path)
    cfg = load_config(cfg_file)
    run_backup(cfg, now=1789347600.0)
    (dest / "20250101-000000").mkdir()  # backup incompleto con datos

    def snapshot(root):
        return {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }, tuple(sorted(str(p.relative_to(root)) for p in root.rglob("*")))

    before = snapshot(dest)
    assert main(["status", "--config", str(cfg_file), "--json"]) == 0
    assert main(["status", "--config", str(cfg_file)]) == 0
    assert snapshot(dest) == before
