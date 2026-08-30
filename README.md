<div align="center">

<img src="site/logo.svg" alt="PragyaLint logo — a gear-and-chain that prunes dead code" width="220" />

# PragyaLint

**Static dead-code analysis for Python that gets rid of the code, too.**

PragyaLint builds a module graph from your entry points, traces what is actually
reachable, and reports — then removes — unused files, exports, functions,
imports, and circular imports. Pure Python. Zero dependencies. One command.

<br />

[![version](https://img.shields.io/pypi/v/pragyalint?style=for-the-badge&label=version&color=7b52ee)](https://pypi.org/project/pragyalint/)
[![python](https://img.shields.io/badge/python-3.11%2B-9d72ff?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/pragyalint/)
[![platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-0d0b1e?style=for-the-badge)](https://github.com/Sanskriti-Studios/PragyaLint/releases)
[![downloads](https://img.shields.io/pypi/dm/pragyalint?style=for-the-badge&logo=pypi&logoColor=white&color=00d2ff)](https://pypi.org/project/pragyalint/)
[![dependencies](https://img.shields.io/badge/dependencies-0-2ea043?style=for-the-badge)](https://github.com/Sanskriti-Studios/PragyaLint/blob/main/pyproject.toml)
[![build](https://img.shields.io/github/actions/workflow/status/Sanskriti-Studios/PragyaLint/tests.yml?style=for-the-badge&logo=github&logoColor=white&color=7b52ee)](https://github.com/Sanskriti-Studios/PragyaLint/actions)
[![license](https://img.shields.io/github/license/Sanskriti-Studios/PragyaLint?style=for-the-badge&color=2ea043)](./LICENSE)

</div>

---

## Why PragyaLint?

- **Reachability, not regex.** A real module graph from your entry points decides
  what is dead — the way a human would.
- **Finds more than imports.** Unreachable modules, unused exports, dead
  functions/classes, unused imports, and circular imports.
- **Confidence-graded.** Every finding is rated `high` / `medium` / `low` so you
  know what to trust and what to double-check.
- **Fixes what it finds.** `--fix` actually removes dead code, gated by
  confidence, with a `--dry-run` preview. Always commit first.
- **Zero runtime deps.** Only the standard library (`ast`). No parser to install,
  nothing to break.
- **Native binaries.** Windows EXE, Linux, and macOS executables on every
  release — no Python required at runtime.

## What it catches

| Rule | Confidence | It reports… |
| --- | --- | --- |
| `unused_file` | high | modules unreachable from any entry point |
| `unused_import` | high | imports never used in their module |
| `unused_export` | medium | public names never imported anywhere |
| `unused_local` | medium/low | functions, classes, variables defined but never used |
| `cycle` | low | circular import cycles |

## Demo

```text
$ pragyalint

src/service.py
  :12       ⚠  [MEDIUM] export 'format_report' of module 'src.service' is never imported
  :31       ✖  [HIGH  ] import 'os' is never used

src/legacy/api.py
           ✖  [HIGH  ] module 'src.legacy.api' is not reachable from any entry point

11 findings in 24 files (20 reachable).
  6 high | 3 medium | 2 low
```

`pragyalint` analyzes the current directory by default. That's it.

## Installation

```bash
pip install pragyalint     # or: pipx install pragyalint
```

Requires Python 3.11+. On Windows use `py -m pragyalint` to run it as a module.

**No Python / no hassle?** Grab a prebuilt executable from the
[Releases](https://github.com/Sanskriti-Studios/PragyaLint/releases) page —
Windows, Linux, and macOS binaries are built and attached automatically on every
`release:` commit.

### Visual Studio Code extension

Find and fix dead code without leaving the editor — findings land in the
**Problems panel**, colored by confidence, plus commands to preview and apply
fixes.

```
code --install-extension IndianCoder3.sks-pragyalint
```

It shells out to the `pragyalint` CLI; set `pragyalint.binaryPath` if it can't
find the binary.

## In your CI

Gate your pipeline on dead code:

```yaml
- uses: actions/checkout@v4
- run: pip install pragyalint
- run: pragyalint --fail-on high --sarif > sarif.json
```

`--fail-on high` exits non-zero when any high-confidence finding exists.
`--sarif` (or `--json`) feeds GitHub code scanning and anything else that
speaks the format.

## Docs

- [Overview](https://github.com/Sanskriti-Studios/PragyaLint/tree/main/site/docs/why.html) — how the analysis works under the hood
- [CLI reference](site/docs/cli-commands.html) — every flag, one table
- [Configuration](site/docs/config.html) — `pragyalint.toml`, `pyproject.toml`, env-friendly defaults
- [Fixes](site/docs/fixes.html) — dry runs, confidence gates, `--force`
- [Errors & troubleshooting](site/docs/errors.html) — Windows/Linux/macOS PATH fixes included
- [Full API](site/docs/api.html) — Python-level usage

## Development

```bash
git clone https://github.com/Sanskriti-Studios/PragyaLint
cd PragyaLint
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## License

[GPL-3.0-or-later](./LICENSE) — free software, keep it that way.