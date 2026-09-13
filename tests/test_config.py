"""Tests del cargador de configuración TOML."""

from pathlib import Path

import pytest

from guardian.config import ConfigError, load_config

VALID = """
[[sources]]
path = "{root}/docs"

[[sources]]
path = "{root}/pictures"

[destination]
path = "{root}/backups"
keep_last = 3
"""


def make_tree(root: Path) -> None:
    (root / "docs").mkdir(parents=True)
    (root / "pictures").mkdir()
    (root / "backups").mkdir()


def test_loads_valid_config(tmp_path):
    make_tree(tmp_path)
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(VALID.format(root=tmp_path), encoding="utf-8")

    cfg = load_config(cfg_file)

    assert cfg.sources == (tmp_path / "docs", tmp_path / "pictures")
    assert cfg.destination.path == tmp_path / "backups"
    assert cfg.destination.keep_last == 3


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="no existe"):
        load_config(tmp_path / "missing.toml")


def test_invalid_toml_raises(tmp_path):
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text("sources = [", encoding="utf-8")
    with pytest.raises(ConfigError, match="TOML inválido"):
        load_config(cfg_file)


def test_missing_sources_raises(tmp_path):
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text('[destination]\npath = "/tmp"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="sources"):
        load_config(cfg_file)


def test_nonexistent_source_dir_raises(tmp_path):
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(
        f'[[sources]]\npath = "{tmp_path}/nope"\n\n[destination]\npath = "{tmp_path}/b"\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="no existe"):
        load_config(cfg_file)


def test_keep_last_must_be_positive(tmp_path):
    (tmp_path / "docs").mkdir()
    cfg_file = tmp_path / "guardian.toml"
    cfg_file.write_text(
        f'[[sources]]\npath = "{tmp_path}/docs"\n\n'
        f'[destination]\npath = "{tmp_path}/b"\nkeep_last = 0\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="keep_last"):
        load_config(cfg_file)
