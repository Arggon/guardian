"""Tests de ``guardian verify``: verificación contra manifiesto (pure read)."""

import json
import shutil

import pytest

from guardian.backup import ManifestError, run_backup
from guardian.cli import main
from guardian.config import load_config
from guardian.verify import (
    BackupNotFoundError,
    resolve_backup,
    run_verify,
    verify_backup,
)


@pytest.fixture()
def environment(tmp_path):
    src = tmp_path / "documentos"
    src.mkdir()
    (src / "nota.txt").write_text("hola guardian", encoding="utf-8")
    sub = src / "sub"
    sub.mkdir()
    (sub / "foto.txt").write_text("0123456789abcdef", encoding="utf-8")
    dest = tmp_path / "backups"
    dest.mkdir()
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(
        f'[[sources]]\npath = "{src}"\n\n[destination]\npath = "{dest}"\n',
        encoding="utf-8",
    )
    return cfg_file, src, dest


def tree_snapshot(root):
    """Mapa ruta-relativa → contenido para comparar árboles (pure read)."""
    return {
        str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_verify_ok_after_backup_exit_0(environment, capsys):
    cfg_file, src, dest = environment
    assert main(["backup", "--config", str(cfg_file)]) == 0
    capsys.readouterr()

    rc = main(["verify", "--config", str(cfg_file)])

    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out
    assert "nota.txt" in out and "foto.txt" in out
    assert "hash-mismatch · 0 faltante" in out


def test_verify_detects_corrupted_byte(environment, capsys):
    cfg_file, src, dest = environment
    run_backup(load_config(cfg_file))
    copied = next(dest.glob("*/documentos/nota.txt"))
    data = bytearray(copied.read_bytes())
    data[0] ^= 0xFF
    copied.write_bytes(bytes(data))

    rc = main(["verify", "--config", str(cfg_file)])

    assert rc == 3
    out = capsys.readouterr().out
    assert "HASH-MISMATCH" in out
    assert "nota.txt" in out


def test_verify_detects_missing_file(environment, capsys):
    cfg_file, src, dest = environment
    run_backup(load_config(cfg_file))
    next(dest.glob("*/documentos/sub/foto.txt")).unlink()

    rc = main(["verify", "--config", str(cfg_file)])

    assert rc == 3
    out = capsys.readouterr().out
    assert "FALTANTE" in out
    assert "foto.txt" in out


def test_verify_without_manifest_is_incomplete_exit_3(environment, capsys):
    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    backup_dir = run_backup(config).backup_dir
    (backup_dir / "manifest.json").unlink()

    rc = main(["verify", "--config", str(cfg_file), "--backup", backup_dir.name])

    assert rc == 3
    assert "incompleto" in capsys.readouterr().err


def test_verify_corrupt_manifest_is_incomplete_exit_3(environment, capsys):
    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    backup_dir = run_backup(config).backup_dir
    (backup_dir / "manifest.json").write_text("{nope", encoding="utf-8")

    rc = main(["verify", "--config", str(cfg_file), "--backup", backup_dir.name])

    assert rc == 3
    assert "incompleto" in capsys.readouterr().err


def test_verify_missing_backup_id_exit_2(environment, capsys):
    cfg_file, src, dest = environment
    run_backup(load_config(cfg_file))

    rc = main(["verify", "--config", str(cfg_file), "--backup", "19990101-000000"])

    assert rc == 2
    assert "no existe" in capsys.readouterr().err


def test_verify_config_error_exit_2(tmp_path, capsys):
    rc = main(["verify", "--config", str(tmp_path / "missing.toml")])
    assert rc == 2
    assert "error de configuración" in capsys.readouterr().err


def test_latest_picks_newest_with_manifest(environment):
    """latest ignora un directorio más nuevo sin manifest.json."""
    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    first = run_backup(config, now=1000000000.0).backup_dir
    run_backup(config, now=1000000300.0)
    incomplete = dest / "20990101-000000"  # más nuevo que todos, sin manifiesto
    incomplete.mkdir()
    shutil.copy(first / "documentos" / "nota.txt", incomplete / "nota.txt")

    resolved = resolve_backup(config, "latest")

    assert resolved == first or resolved.name > first.name
    assert resolved != incomplete
    assert (resolved / "manifest.json").is_file()


def test_latest_without_any_complete_backup_exit_2(environment, capsys):
    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    run_backup(config)
    next(dest.glob("*/manifest.json")).unlink()

    rc = main(["verify", "--config", str(cfg_file)])

    assert rc == 2
    assert "completos" in capsys.readouterr().err


def test_verify_backup_reports_statuses(environment):
    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    backup_dir = run_backup(config).backup_dir
    (backup_dir / "documentos" / "sub" / "foto.txt").write_text("corrupto!", encoding="utf-8")
    (backup_dir / "documentos" / "nota.txt").unlink()

    result = verify_backup(backup_dir)

    by_source = {v.source: v for v in result.verdicts}
    assert by_source["nota.txt"].status == "missing"
    assert by_source["sub/foto.txt"].status == "hash-mismatch"
    assert result.exit_code == 3
    assert result.ok_count == 0


def test_verify_missing_file_and_mixed_statuses(environment):
    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    backup_dir = run_backup(config).backup_dir
    (backup_dir / "documentos" / "nota.txt").unlink()

    _, result = run_verify(config, backup_dir.name)

    assert result.missing[0].source == "nota.txt"
    assert result.ok_count == 1  # sub/foto.txt sigue bien
    assert result.exit_code == 3


def test_verify_is_pure_read(environment, capsys):
    """El árbol del destino queda byte a byte idéntico tras verify."""
    cfg_file, src, dest = environment
    run_backup(load_config(cfg_file))
    # un directorio incompleto además: verify (latest) tampoco debe tocarlo
    (dest / "20990101-000000").mkdir()
    before = tree_snapshot(dest)

    rc = main(["verify", "--config", str(cfg_file)])
    assert rc == 0

    assert tree_snapshot(dest) == before


def test_manifest_destination_is_relative_to_backup_root(environment):
    """docs/FORMAT.md: destination = <nombre-origen>/<path> relativa a la raíz."""
    import json

    cfg_file, src, dest = environment
    backup_dir = run_backup(load_config(cfg_file)).backup_dir
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    entries = {e["path"]: e["destination"] for e in manifest["sources"][0]["files"]}
    assert entries["nota.txt"] == "documentos/nota.txt"
    assert entries["sub/foto.txt"] == "documentos/sub/foto.txt"


def test_verify_module_raises_not_found_for_bad_id(environment):
    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    with pytest.raises(BackupNotFoundError):
        resolve_backup(config, "no-existe")
    with pytest.raises(BackupNotFoundError):
        run_verify(config, "19991231-235959")


def test_verify_module_missing_manifest_raises_manifest_error(environment):
    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    backup_dir = run_backup(config).backup_dir
    (backup_dir / "manifest.json").unlink()
    with pytest.raises(ManifestError):
        verify_backup(backup_dir)


def test_cli_verify_help_documents_exit_codes(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["verify", "--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for code in ("0", "2", "3"):
        assert code in out
    assert "incompleto" in out


def test_verify_reads_manifest_with_failed_source(environment):
    """Un backup parcial: los archivos ok se verifican; nada explota."""

    cfg_file, src, dest = environment
    config = load_config(cfg_file)
    backup_dir = run_backup(config).backup_dir
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    # simulamos una entrada failed sin files, como la escribe checker-core
    manifest["sources"].append({"root": str(src.parent / "otro"), "status": "failed"})
    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    _, result = run_verify(config, backup_dir.name)

    assert result.ok_count == 2
    assert result.exit_code == 0
