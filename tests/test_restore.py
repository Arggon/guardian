"""Tests del restore: reconstrucción verificada desde un backup."""

import json

import pytest

from guardian.backup import run_backup
from guardian.config import load_config
from guardian.restore import (
    DestNotEmptyError,
    RestoreError,
    RestoreHashMismatch,
    run_restore,
)
from guardian.verify import BackupNotFoundError


@pytest.fixture()
def environment(tmp_path):
    src = tmp_path / "documentos"
    (src / "sub").mkdir(parents=True)
    (src / "nota.txt").write_text("hola guardian", encoding="utf-8")
    (src / "sub" / "foto.bin").write_bytes(b"\x00\x01\x02" * 100)
    dest_root = tmp_path / "backups"
    dest_root.mkdir()
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(
        f'[[sources]]\npath = "{src}"\n\n[destination]\npath = "{dest_root}"\n',
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    result = run_backup(cfg, now=1789347600.0)
    return cfg, cfg_file, src, dest_root, result.backup_dir


def read_tree(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_restore_roundtrip_recreates_origins(environment, tmp_path):
    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "salida"
    out.mkdir()

    result = run_restore(cfg, backup_dir.name, out)

    assert result.files == 2
    assert result.bytes > 0
    # dest/<nombre-origen>/ reproduce el árbol original bit a bit
    assert read_tree(out / "documentos") == read_tree(src)


def test_restore_missing_backup_raises(environment, tmp_path):
    cfg, *_ , _ = environment
    out = tmp_path / "salida2"
    out.mkdir()
    with pytest.raises(BackupNotFoundError, match="no existe el backup"):
        run_restore(cfg, "19990101-000000", out)


def test_restore_latest_picks_newest_complete(environment, tmp_path):
    cfg, cfg_file, src, dest_root, backup_dir = environment
    (src / "nuevo.txt").write_text("segunda corrida", encoding="utf-8")
    run_backup(cfg, now=1789347600.0 + 3600)
    out = tmp_path / "salida3"
    out.mkdir()

    run_restore(cfg, "latest", out)

    assert (out / "documentos" / "nuevo.txt").read_text(encoding="utf-8") == "segunda corrida"


def test_restore_dest_not_empty_requires_overwrite(environment, tmp_path):
    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "salida4"
    out.mkdir()
    (out / "preexistente.txt").write_text("algo", encoding="utf-8")

    with pytest.raises(DestNotEmptyError, match="--overwrite"):
        run_restore(cfg, backup_dir.name, out)

    # con --overwrite procede (y no borra lo preexistente: pisa solo lo suyo)
    run_restore(cfg, backup_dir.name, out, overwrite=True)
    assert (out / "preexistente.txt").exists()
    assert (out / "documentos" / "nota.txt").exists()


def test_restore_dest_existing_empty_dir_ok(environment, tmp_path):
    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "salida5"
    out.mkdir()
    run_restore(cfg, backup_dir.name, out)
    assert (out / "documentos" / "nota.txt").exists()


def test_restore_detects_corrupted_backup_file(environment, tmp_path):
    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "salida6"
    out.mkdir()
    # corrompemos la copia del backup (no el origen)
    target = backup_dir / "documentos" / "nota.txt"
    target.write_text("contenido corrompido", encoding="utf-8")

    with pytest.raises(RestoreHashMismatch, match="hash-mismatch"):
        run_restore(cfg, backup_dir.name, out)

    # el archivo corrupto NUNCA llega al destino
    assert not (out / "documentos" / "nota.txt").exists()


def test_restore_missing_file_in_backup_raises(environment, tmp_path):
    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "salida7"
    out.mkdir()
    (backup_dir / "documentos" / "nota.txt").unlink()

    with pytest.raises(RestoreError, match="ausente en el backup"):
        run_restore(cfg, backup_dir.name, out)


def test_restore_incomplete_backup_manifest_raises(environment, tmp_path):
    from guardian.backup import ManifestError, manifest_path

    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "salida8"
    out.mkdir()
    manifest_path(backup_dir).unlink()

    with pytest.raises(ManifestError, match="no existe"):
        run_restore(cfg, backup_dir.name, out)


def test_restore_never_writes_into_backup(environment, tmp_path):
    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "salida9"
    out.mkdir()
    before = read_tree(backup_dir)
    before_manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))

    run_restore(cfg, backup_dir.name, out)

    assert read_tree(backup_dir) == before
    after_manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert after_manifest == before_manifest


def test_restore_creates_dest_if_missing(environment, tmp_path):
    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "no-existe-todavia"

    run_restore(cfg, backup_dir.name, out)

    assert (out / "documentos" / "sub" / "foto.bin").read_bytes() == b"\x00\x01\x02" * 100


def test_restore_works_after_source_deleted(environment, tmp_path):
    """El caso de uso real: el origen ya no está y lo recuperamos del backup.

    Regresión de bug-restore-enosource: load_config no debe exigir fuentes
    existentes cuando el comando es restore (solo usa destination).
    """
    cfg, cfg_file, src, dest_root, backup_dir = environment
    out = tmp_path / "recuperado"

    import shutil

    shutil.rmtree(src)  # el origen desaparece

    result = run_restore(cfg, backup_dir.name, out)

    assert (out / "documentos" / "nota.txt").read_text(encoding="utf-8") == "hola guardian"
    assert result.files == 2
