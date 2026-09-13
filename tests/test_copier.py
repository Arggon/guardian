"""Tests del motor de copia y verificación SHA-256."""

from pathlib import Path

import pytest

from guardian.copier import HashMismatch, copy_file, copy_tree, hash_file, iter_files


def test_hash_file_known_vector(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_bytes(b"hello world")
    # sha256("hello world")
    assert hash_file(f) == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_hash_file_large_file_streams(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"\x00" * (5 << 20))  # 5 MiB, más de un chunk
    assert len(hash_file(f)) == 64


def test_copy_file_copies_and_verifies(tmp_path):
    src_root = tmp_path / "src"
    (src_root / "sub").mkdir(parents=True)
    f = src_root / "sub" / "a.txt"
    f.write_text("contenido", encoding="utf-8")

    record = copy_file(src_root, f, tmp_path / "backup")

    copied = tmp_path / "backup" / "sub" / "a.txt"
    assert copied.read_text(encoding="utf-8") == "contenido"
    assert record.source == "sub/a.txt"
    assert record.destination == "sub/a.txt"
    assert record.size == len("contenido")
    assert record.sha256 == hash_file(f)


def test_copy_file_dry_run_writes_nothing(tmp_path):
    src_root = tmp_path / "src"
    src_root.mkdir()
    f = src_root / "a.txt"
    f.write_text("x", encoding="utf-8")

    record = copy_file(src_root, f, tmp_path / "backup", dry_run=True)

    assert not (tmp_path / "backup").exists()
    assert record.sha256 == hash_file(f)


def test_copy_file_detects_corrupted_copy(tmp_path, monkeypatch):
    src_root = tmp_path / "src"
    src_root.mkdir()
    f = src_root / "a.txt"
    f.write_text("datos importantes", encoding="utf-8")

    real_hash = hash_file

    def lying_hash(path: Path) -> str:
        # el origen hashea bien; la copia recién creada hashea "distinto"
        return real_hash(path) if path == f else "0" * 64

    monkeypatch.setattr("guardian.copier.hash_file", lying_hash)

    with pytest.raises(HashMismatch, match="verificación fallida"):
        copy_file(src_root, f, tmp_path / "backup")

    assert not list((tmp_path / "backup").rglob("*"))  # la copia corrupta se descarta


def test_copy_tree_recursive_sorted_and_skips_symlinks(tmp_path):
    src_root = tmp_path / "src"
    (src_root / "b").mkdir(parents=True)
    (src_root / "a.txt").write_text("a", encoding="utf-8")
    (src_root / "b" / "c.txt").write_text("c", encoding="utf-8")
    (src_root / "dangling").symlink_to(src_root / "no-such-file")

    records = copy_tree(src_root, tmp_path / "backup", dry_run=True)

    assert [r.source for r in records] == ["a.txt", "b/c.txt"]


def test_iter_files_ignores_empty_dirs(tmp_path):
    src_root = tmp_path / "src"
    (src_root / "empty").mkdir(parents=True)
    (src_root / "f.txt").write_text("f", encoding="utf-8")

    assert list(iter_files(src_root)) == [src_root / "f.txt"]
