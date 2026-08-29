"""Command-line interface for PragyaLint."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from pragyalint import __version__
from pragyalint.analyzer import analyze
from pragyalint.config import ConfigError, load_config
from pragyalint.models import Confidence, should_fail
from pragyalint.reporters import format_json, format_sarif, format_terminal

AVAILABLE_RULES = [
    "unused_file",
    "unused_export",
    "unused_import",
    "unused_local",
    "cycle",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pragyalint",
        description="Static dead-code analyzer for Python projects.",
    )
    parser.add_argument("--version", action="version", version=f"PragyaLint {__version__}")
    parser.add_argument(
        "-r", "--root-dir",
        default=None,
        help="Root directory of the project. Defaults to the current directory.",
    )
    parser.add_argument(
        "-e", "--entry", nargs="*", default=None,
        help="Entry-point modules, globs, or file paths.",
    )
    parser.add_argument(
        "-i", "--ignore", nargs="*", default=None,
        help="Glob patterns to ignore.",
    )
    parser.add_argument(
        "-x", "--extensions", nargs="*", default=None,
        help="File extensions to analyze. Default: .py",
    )
    parser.add_argument(
        "--include", nargs="*", default=None,
        help="Only analyze files under these paths.",
    )
    parser.add_argument(
        "--rules", nargs="*", default=None,
        choices=AVAILABLE_RULES,
        help="Restrict analysis to the given rules.",
    )
    parser.add_argument(
        "--no-report-unused-exports", action="store_true",
        help="Disable unused-export reporting.",
    )
    parser.add_argument(
        "--no-conventional-entries", action="store_true",
        help="Exclude conventional entries (main.py, app.py, __main__.py, setup.py).",
    )
    parser.add_argument(
        "--include-entry-exports", action="store_true",
        help="Report unused exports declared in entry files.",
    )
    parser.add_argument(
        "--ignore-tests", action="store_true",
        help="Ignore test files and directories.",
    )
    parser.add_argument(
        "--cycles", action="store_true",
        help="Detect and report circular import cycles.",
    )
    parser.add_argument(
        "--fail-on",
        choices=["high", "medium", "low", "none"],
        default=None,
        help="Exit non-zero when findings meet this confidence threshold.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print the structured report as JSON.",
    )
    parser.add_argument(
        "--sarif", action="store_true",
        help="Print SARIF output.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Print verbose output and internal graph state.",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable ANSI colors in terminal output.",
    )
    parser.add_argument(
        "--fix", nargs="*", default=None,
        choices=["files", "imports", "exports"],
        help="Fix targets to apply: files, imports, exports. Defaults to all.",
    )
    parser.add_argument(
        "--confidence", choices=["high", "medium+", "low+", "all"],
        default=None,
        help="Minimum fix confidence: high, medium+, low+, or all.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Log planned fixes without changing files.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Allow a selected fix when the source edit is otherwise considered unsafe.",
    )
    return parser


def _pick_root(cli_value: Optional[str], config: dict) -> str:
    if cli_value:
        return cli_value
    candidate = config.get("root_dir") or "."
    return os.path.abspath(candidate)


def _merge_option(cli_value, config: dict, key: str):
    if cli_value is not None:
        return cli_value
    return config.get(key)


def _conf_str(value: str) -> str:
    return value


def _confidence_min(value: Optional[str]) -> str:
    """Map a --confidence value to a single minimum confidence level."""
    if value is None:
        return "high"
    mapping = {"high": "high", "medium+": "medium", "low+": "low", "all": "low"}
    return mapping.get(value, "high")


def _print_fix_summary(fix_result, dry_run: bool) -> None:
    from pragyalint.fixer import FixResult

    if not isinstance(fix_result, FixResult):
        return
    label = "Would" if dry_run else "Did"
    for action in fix_result.dry_run:
        print(f"  [dry-run] {label}: {action}")
    for action in fix_result.applied:
        print(f"  [fixed]   {action}")
    for action in fix_result.skipped:
        print(f"  [skipped] {action}")
    if not (fix_result.applied or fix_result.dry_run or fix_result.skipped):
        print("  No fixes applied.")


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load configuration first so defaults can come from config file.
    cli_root = args.root_dir
    config = {}
    if cli_root:
        root_for_config = cli_root
    else:
        root_for_config = os.getcwd()
    try:
        config = load_config(root_for_config)
    except ConfigError as exc:
        print(f"pragyalint: error: {exc}", file=sys.stderr)
        return 2

    root_dir = _pick_root(cli_root, config)

    entry = _merge_option(args.entry, config, "entry") or []
    ignore = _merge_option(args.ignore, config, "ignore") or []
    extensions = _merge_option(args.extensions, config, "extensions") or [".py"]
    include = _merge_option(args.include, config, "include") or []
    rules = _merge_option(args.rules, config, "rules") or []
    detect_cycles = args.cycles or bool(config.get("detect_cycles"))
    include_entry_exports = args.include_entry_exports or bool(
        config.get("include_entry_exports")
    )
    ignore_tests = args.ignore_tests or bool(config.get("ignore_tests"))
    conventional_entries = not (args.no_conventional_entries or not config.get(
        "conventional_entries", True
    ))

    if args.no_report_unused_exports:
        rules = ([r for r in rules if r != "unused_export"] or
                 [r for r in AVAILABLE_RULES if r != "unused_export"])

    report = analyze(
        root_dir=root_dir,
        entry=entry,
        ignore=ignore,
        extensions=extensions,
        include=include,
        rules=rules if rules else None,
        report_unused_exports=True,
        conventional_entries=conventional_entries,
        include_entry_exports=include_entry_exports,
        ignore_tests=ignore_tests,
        detect_cycles=detect_cycles,
    )

    if args.fix is not None:
        from pragyalint.fixer import apply_fixes

        targets = args.fix if args.fix else ["files", "imports", "exports"]
        min_conf = _confidence_min(args.confidence)
        fix_result = apply_fixes(
            report,
            targets=targets,
            min_confidence=min_conf,
            dry_run=args.dry_run,
            force=args.force,
        )
        _print_fix_summary(fix_result, dry_run=args.dry_run)
        if not args.json and not args.sarif:
            print()

    if args.json:
        print(format_json(report))
    elif args.sarif:
        print(format_sarif(report))
    else:
        print(format_terminal(report, color=not args.no_color))
        if args.verbose:
            print("\n[verbose] entry points:", ", ".join(report.entry_points) or "(none)")
            print("[verbose] modules:")
            for record in report.modules:
                flag = "R" if record.reachable else "D"
                print(f"  {flag} {record.module_name:<30} {record.path}")

    fail_threshold = (
        args.fail_on if args.fail_on else config.get("fail_on")
    )
    if fail_threshold and fail_threshold != "none":
        if should_fail(report, Confidence.parse_min(fail_threshold)):
            return 1
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    try:
        return run(argv)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
