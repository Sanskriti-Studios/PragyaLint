# PragyaLint 🔍

A **static dead-code analyzer for Python**. PragyaLint builds a module graph from your
entry points, traces what's actually reachable, and reports unused files, exports,
functions, imports, and circular imports — so you can keep your codebase lean.

Inspired by [OptiPrune](https://github.com/optiprune/cli) (a dead-code analyzer for
TypeScript/JavaScript) — PragyaLint brings the same concept to Python.

---

## Features

| Area | What is included |
| --- | --- |
| **Project analysis** | Entry discovery, module graph, reachability, import-cycle reporting |
| **Python** | `.py` files and packages, `__init__.py`, relative imports, dynamic imports |
| **Dead code** | Unreachable modules/files, unused public exports, unused functions/classes, unused imports, unused assignments |
| **Confidence levels** | Every finding is rated `high`, `medium`, or `low` so you know how much to trust it |
| **Output** | Human-readable terminal output, JSON reports, and SARIF for CI/code-scanning workflows |
| **CI-ready** | `--fail-on <confidence>` gates your pipeline on dead-code findings |
| **Configuration** | `pragyalint.toml`, `pragyalint.json`, or `[tool.pragyalint]` in `pyproject.toml` |
| **Opt-in fixes** | `--fix` actually removes dead code — confidence-gated with `--dry-run` |
| **Zero dependencies** | Uses only the Python standard library — no `pip install` deps, no parser to ship |

---

## Installation

### Command-line tool

```bash
pip install pragyalint
# or
pipx install pragyalint
# or
pip install --user pragyalint
```

Requires Python 3.11+.

### Visual Studio Code extension

Install **PragyaLint for Visual Studio Code** from the Marketplace:

- **Marketplace:** https://marketplace.visualstudio.com/items?itemName=IndianCoder3.sks-pragyalint
- **Install via command line:** `code --install-extension IndianCoder3.sks-pragyalint`
- Or open the Extensions panel (`Ctrl+Shift+X`) and search for **"PragyaLint"**.

The extension publishes dead-code findings to the **Problems panel** (colored by
confidence) and provides commands to preview and apply fixes from the editor:

| Command | What it does |
| --- | --- |
| `PragyaLint: Scan workspace` | Reports dead code into the Problems panel |
| `PragyaLint: Preview fixes (dry-run)` | Shows planned changes, no edits |
| `PragyaLint: Apply safe fixes` | Applies high-confidence fixes |
| `PragyaLint: Scan and remove dead code (all confidence)` | Full prune |

It requires the `pragyalint` CLI on your PATH (see above). If the CLI isn't found,
set the `pragyalint.binaryPath` setting to the full path of the executable. The
extension also auto-detects common `pipx`/`pip` install locations.

## Quick start

Run an analysis from the project root:

```bash
pragyalint
```

Specify entry points and output formats:

```bash
pragyalint --entry src/main.py
pragyalint --json
pragyalint --sarif > pragyalint.sarif
```

## Commands

| Command | Purpose |
| --- | --- |
| `pragyalint` | Analyze the project (default command) |
| `pragyalint --json` | Print the structured report as JSON |
| `pragyalint --sarif` | Print SARIF output for CI |
| `pragyalint --help` | Print command and option help |
| `pragyalint --version` | Print the version |

## Analyze flags

| Flag | Description | Default |
| --- | --- | --- |
| `-r, --root-dir <path>` | Root directory of the project | current directory |
| `-e, --entry <module...>` | Entry-point modules, globs, or file paths | auto-detect |
| `-i, --ignore <patterns...>` | Glob patterns to ignore | `[]` |
| `-x, --extensions <exts...>` | File extensions to analyze | `.py` |
| `--include <paths...>` | Only analyze files under these paths | `[]` |
| `--rules <rules...>` | Restrict analysis to specific rules | all |
| `--no-report-unused-exports` | Disable unused-export reporting | enabled |
| `--no-conventional-entries` | Exclude conventional entries (`main.py`, `app.py`, ...) | included |
| `--include-entry-exports` | Report unused exports in entry files | disabled |
| `--ignore-tests` | Ignore test files and directories | disabled |
| `--cycles` | Report circular import cycles | disabled |
| `--fail-on <confidence>` | Exit non-zero at/above this confidence | — |
| `--json` | JSON output | — |
| `--sarif` | SARIF output | — |
| `--no-color` | Disable ANSI colors | — |
| `-v, --verbose` | Print internal graph state | — |
| `--fix <targets...>` | Apply fixes: `files`, `imports`, `exports` | — |
| `--confidence <level>` | Minimum fix confidence: `high`, `medium+`, `low+`, `all` | `high` |
| `--dry-run` | Log planned fixes without changing files | — |
| `--force` | Allow a fix considered unsafe (e.g. `__all__`-listed exports) | — |

## Rules / finding types

| Rule | Confidence | What it finds |
| --- | --- | --- |
| `unused_file` | `high` | Modules unreachable from any entry point |
| `unused_import` | `high` | Imports never used in their module |
| `unused_export` | `medium` | Public names never imported anywhere |
| `unused_local` | `medium`/`low` | Functions/classes/variables defined but never used |
| `cycle` | `low` | Circular import cycles |

## Confidence

Every finding carries a confidence level:

- **high** — structurally certain (module unreachable, import unused)
- **medium** — strongly implied (export/definition not referenced)
- **low** — heuristic (constant assignments, cycles)

Use `--fail-on` to make your CI fail on a given threshold, e.g.:

```bash
pragyalint --fail-on high
```

This exits with a non-zero code when any `high`-confidence finding exists — perfect for
blocking PRs that introduce dead code.

## Fixes

Like OptiPrune, PragyaLint's fixer is **explicit, not implicit**. Analysis only reports;
use `--fix` to actually remove dead code. Always start with a dry run, inspect the
output, then drop `--dry-run`.

```bash
# Preview what would change (does NOT modify files)
pragyalint --fix --dry-run

# Actually remove dead code
pragyalint --fix

# Remove dead code and functions with lower-risk edits too
pragyalint --fix exports --confidence medium+
```

| Target | What it does |
| --- | --- |
| `files` | Delete unreachable modules (never deletes entries or `__init__.py`) |
| `imports` | Remove unused imports; trims unused names from multi-name imports |
| `exports` | Remove unused function/class/variable definitions (respects `__all__`) |

Fixes are confidence-gated:

- `--confidence high` (default) — only high-confidence removals.
- `--confidence medium+` — also remove unused exports/definitions.
- `--force` — allow an edit otherwise considered unsafe (e.g. removing a name
  listed in `__all__`).

> **Always commit before fixing.** Removing code can have ripple effects. Run
> `--dry-run` first and re-run after fixing.

## Configuration

PragyaLint loads configuration from the first file it finds (starting at the root
directory):

1. `pragyalint.toml`
2. `pragyalint.json`
3. `[tool.pragyalint]` section of `pyproject.toml`

```toml
# pragyalint.toml
entry = ["src"]
ignore = ["migrations/", "generated/"]
extensions = [".py"]
detect_cycles = true
fail_on = "medium"
```

Or inside your `pyproject.toml`:

```toml
[tool.pragyalint]
ignore = ["tests/"]
report_unused_exports = false
```

## Why Python for analyzing Python?

PragyaLint is written in pure Python and relies on the standard-library `ast` module.
That gives you:

- A **complete, battle-tested Python parser** with zero external dependencies
- Correct handling of every modern Python syntax construct
- Simple distribution via PyPI / `pipx`
- No parser to build or maintain

## Development

```bash
git clone https://github.com/example/pragyalint
cd pragyalint
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

[GPL-3.0-or-later](./LICENSE)
