<!-- arggon:generated template="CHANGELOG.md" -->
# Changelog

All notable changes to guardian are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `guardian restore <backup|latest> --dest [--overwrite]`: reconstrucción verificada contra el manifiesto (PR final del pipeline v0.2).

- `guardian verify [--backup <id|latest>]`: verifica un backup recomputando
  SHA-256 de cada archivo contra su `manifest.json`; reporta ok /
  hash-mismatch / faltante por archivo y exit 3 ante cualquier divergencia o
  manifiesto ausente. Pure read: nunca escribe en el destino. (issue #2)

### Fixed

- El campo `destination` del manifiesto ahora es relativo a la raíz del backup
  (`<nombre-origen>/<path>`), como define docs/FORMAT.md; antes quedaba
  relativo al subdirectorio del origen. (issue #2)

### Changed

- <!-- for changes in existing functionality -->

### Deprecated

- <!-- for soon-to-be removed features -->

### Removed

- <!-- for now removed features -->

### Fixed

- <!-- for any bug fixes -->

### Security

- <!-- in case of vulnerabilities -->

<!--
[1.0.0] - 2026-MM-DD — example release stub; replace dates and versions as you tag releases.
-->
