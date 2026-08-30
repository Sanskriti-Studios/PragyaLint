# Changelog

All notable changes to PragyaLint are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.4] - 2026-08-30

### Added

- Windows compatibility end to end:
  - Terminal/JSON/SARIF output is UTF-8-safe on Windows consoles and
    non-UTF-8 locales — the Unicode markers no longer crash the CLI when
    output is piped or redirected.
  - The fixer preserves CRLF line endings (and no longer mangles them via
    universal-newline translation).
  - The VS Code extension auto-detects `pip --user` / pipx binaries in the
    standard Windows locations (`%APPDATA%\Python\Scripts`, pipx `Scripts`).
- 16 documentation pages complete the docs site (why/how-it-works, CLI
  reference, reports, cache, integrations, automation, plugins, VS Code, API,
  contributing, source).
- README rebuilt with `for-the-badge` badges, the brand logo, and prebuilt
  binary install instructions.
- Release pipeline: a `release:` commit now always produces a GitHub Release
  with the PyPI wheel, Windows/Linux/macOS binaries, and the VSIX attached.
  A separate workflow builds the VSIX and can publish it to the Marketplace
  when a `VSCE_PAT` secret is configured.

### Changed

- `pragyalint/__init__.py` version is kept in sync with `pyproject.toml`, so
  release tags always agree with `pragyalint --version`.
- `LICENSE` updated to the canonical GPL-3.0 text.

## [0.1.1] - 2026-08-29

### Changed

- Visual Studio Code extension ships its own packaged `.vsix` (publisher
  `IndianCoder3`) with an icon, license, and homepage metadata.
- VS Code extension auto-detects the `pragyalint` binary in common pipx/pip
  locations and surfaces a helpful message when it cannot be found.
- Package author field anonymized to `IndianCoder3`.

## [0.1.0] - 2026-08-29

### Added

- **Fix engine** (`--fix`) — opt-in removal of dead code, confidence-gated with
  dry-run support:
  - `files`: delete unreachable modules (never entries or `__init__.py`).
  - `imports`: remove unused imports; trims unused names from multi-name imports.
  - `exports`: remove unused function/class/variable definitions (respects `__all__`).
  - `--confidence high|medium+|low+|all`, `--dry-run`, and `--force` flags.
- Module graph builder using the standard-library `ast` module.
  - Entry discovery (conventional entries: `main.py`, `app.py`, `__main__.py`,
    `setup.py`) and explicit `--entry` support.
  - Package/`__init__.py` handling and relative import resolution.
  - Dynamic import detection (`importlib.import_module`, `__import__`).
  - Qualified member-access tracking (`helper.used()` counts as a usage).
  - Reachability analysis and strongly-connected-component cycle detection.
- Dead-code finders:
  - `unused_file` (high): unreachable modules.
  - `unused_import` (high): unused imports, honoring `__all__` re-exports.
  - `unused_export` (medium): defined public names never imported.
  - `unused_local` (medium/low): unused functions, classes, and assignments.
  - `cycle` (low): circular import cycles.
- Confidence levels on every finding (`high` / `medium` / `low`).
- Terminal, JSON, and SARIF reporters.
- `--fail-on <confidence>` CI gating.
- Configuration via `pragyalint.toml`, `pragyalint.json`, or
  `[tool.pragyalint]` in `pyproject.toml`.
- Zero runtime dependencies; requires Python 3.9+.
- Test suite (pytest) and GitHub Actions CI with a self-analysis gate.
