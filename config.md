# Configuration reference

PragyaLint loads its configuration from the first matching source, searched in
this order (all relative to the analysis root):

1. `pragyalint.toml`
2. `pragyalint.json`
3. the `[tool.pragyalint]` table inside `pyproject.toml`

Command-line flags always override configuration values.

## Options

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `root_dir` | `string` | `"."` | Root directory of the project. |
| `entry` | `list[string]` | `[]` | Entry-point modules, globs, or file paths. |
| `ignore` | `list[string]` | `[]` | Glob patterns to ignore. |
| `extensions` | `list[string]` | `[".py"]` | File extensions to analyze. |
| `include` | `list[string]` | `[]` | Only analyze files under these paths. |
| `rules` | `list[string]` | `[]` | Restrict analysis to the listed rules (empty = all). |
| `report_unused_exports` | `bool` | `true` | Enable/disable unused-export reporting. |
| `conventional_entries` | `bool` | `true` | Use conventional entries (`main.py`, `app.py`, `__main__.py`, `setup.py`). |
| `include_entry_exports` | `bool` | `false` | Report unused exports in entry files. |
| `ignore_tests` | `bool` | `false` | Ignore test files and directories. |
| `detect_cycles` | `bool` | `false` | Detect and report circular imports. |
| `fail_on` | `string` | `null` | Exit non-zero at/above this confidence: `high`, `medium`, `low`, `none`. |
| `output` | `string` | `"terminal"` | Reserved for future output selection. |

Unknown keys are ignored.

## Examples

### `pragyalint.toml`

```toml
entry = ["src/main.py"]
ignore = ["migrations/", "generated/"]
detect_cycles = true
fail_on = "medium"
report_unused_exports = true
```

### `pyproject.toml`

```toml
[tool.pragyalint]
ignore = ["tests/", "scripts/"]
include_entry_exports = false
```

### Rules

The `unused_*`/`cycle` rule names are listed in the README. For example, to run
only file- and import-level analysis:

```toml
rules = ["unused_file", "unused_import"]
```
