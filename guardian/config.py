"""Carga de configuración TOML: carpetas origen y destino de los backups."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """La configuración es inválida o incompleta."""


@dataclass(frozen=True)
class Destination:
    path: Path
    keep_last: int = 5

    def __post_init__(self) -> None:
        if self.keep_last < 1:
            raise ConfigError(f"keep_last debe ser >= 1 (got {self.keep_last})")


@dataclass(frozen=True)
class Config:
    sources: tuple[Path, ...]
    destination: Destination


def load_config(path: Path, *, require_sources_exist: bool = True) -> Config:
    """Lee un archivo TOML y devuelve la Config validada.

    Formato esperado::

        [[sources]]
        path = "/home/arggon/Documents"

        [destination]
        path = "/mnt/backup/guardian"
        keep_last = 5

    Con ``require_sources_exist=False`` las carpetas origen no necesitan existir
    (restore: el caso de uso es precisamente que el origen ya no esté).
    """
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"no existe el archivo de configuración: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"TOML inválido en {path}: {exc}") from exc

    sources_raw = raw.get("sources")
    if not sources_raw or not isinstance(sources_raw, list):
        raise ConfigError("falta la tabla [[sources]] (al menos una carpeta origen)")

    sources: list[Path] = []
    for i, entry in enumerate(sources_raw):
        value = entry.get("path") if isinstance(entry, dict) else None
        if not value:
            raise ConfigError(f"sources[{i}] no define 'path'")
        source = Path(value).expanduser().resolve()
        if require_sources_exist and not source.is_dir():
            raise ConfigError(f"la carpeta origen no existe o no es un directorio: {source}")
        sources.append(source)

    dest_raw = raw.get("destination")
    if not dest_raw or not isinstance(dest_raw, dict) or not dest_raw.get("path"):
        raise ConfigError("falta [destination] con su 'path'")
    dest_path = Path(dest_raw["path"]).expanduser().resolve()
    if dest_path.exists() and not dest_path.is_dir():
        raise ConfigError(f"el destino existe y no es un directorio: {dest_path}")

    keep_last = dest_raw.get("keep_last", 5)
    if not isinstance(keep_last, int):
        raise ConfigError("keep_last debe ser un entero")

    return Config(
        sources=tuple(sources),
        destination=Destination(path=dest_path, keep_last=keep_last),
    )
