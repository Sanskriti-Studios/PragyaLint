# PragyaLint for VS Code

Find and remove **dead code** in Python: unreachable modules, unused imports,
exports, and functions.

Powered by [PragyaLint](https://github.com/abhinu/pragyalint) (GPL-3.0-or-later).

## Features

- **Scan** — runs `pragyalint --json` on your workspace and publishes findings
  to the Problems panel, colored by confidence (error/warning/info).
- **Dry-run preview** — `--fix --dry-run` output opens in a read-only document.
- **Apply fixes** — runs `--fix` at the configured confidence.
- **Clean all** — `--fix --confidence low+ --force` for a full prune.

## Requirements

- Python 3.9+
- `pragyalint` on your PATH (`pip install pragyalint`)

## Commands

| Command | Description |
| --- | --- |
| `PragyaLint: Scan workspace` | Report dead code into the Problems panel |
| `PragyaLint: Preview fixes (dry-run)` | Show planned changes, no edits |
| `PragyaLint: Apply safe fixes` | Apply high-confidence fixes |
| `PragyaLint: Scan and remove dead code (all confidence)` | Full prune |

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| `pragyalint.binaryPath` | `pragyalint` | Executable path |
| `pragyalint.confidence` | `high` | Minimum fix confidence |
| `pragyalint.showLowConfidence` | `true` | Show low-confidence findings |

## Building

```bash
npm install
npm run compile
# package a .vsix
npm run package
```

## License

GPL-3.0-or-later