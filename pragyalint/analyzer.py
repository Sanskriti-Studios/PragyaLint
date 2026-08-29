"""Orchestrate the analysis pipeline: build graph, run finders, produce report."""

from __future__ import annotations

from pragyalint.graph import ModuleGraphBuilder
from pragyalint.models import AnalysisReport


def default_hooks() -> dict:
    """Return the default mapping of rule name -> finder class."""
    from pragyalint.finders.unused_files import UnusedFilesFinder
    from pragyalint.finders.unused_exports import UnusedExportsFinder
    from pragyalint.finders.unused_imports import UnusedImportsFinder
    from pragyalint.finders.unused_local import UnusedLocalFinder
    from pragyalint.finders.cycles import CycleFinder

    return {
        "unused_file": UnusedFilesFinder,
        "unused_export": UnusedExportsFinder,
        "unused_import": UnusedImportsFinder,
        "unused_local": UnusedLocalFinder,
        "cycle": CycleFinder,
    }


def analyze(
    root_dir: str,
    entry: Optional[List[str]] = None,
    ignore: Optional[List[str]] = None,
    extensions: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    rules: Optional[List[str]] = None,
    report_unused_exports: bool = True,
    conventional_entries: bool = True,
    include_entry_exports: bool = False,
    ignore_tests: bool = False,
    detect_cycles: bool = False,
    fail_on: Optional[str] = None,
    include_deps: bool = False,
    hooks: Optional[dict] = None,
) -> AnalysisReport:
    """Run a full analysis and return an :class:`AnalysisReport`."""
    if entry is None:
        entry = []
    if ignore is None:
        ignore = []
    if extensions is None:
        extensions = [".py"]

    tests_ignore = [
        "test",
        "tests",
        "__tests__",
        "conftest.py",
        "test_*.py",
        "*_test.py",
        "*.py",
    ]
    effective_ignore = list(ignore)
    if ignore_tests:
        effective_ignore.extend(tests_ignore)

    graph = ModuleGraphBuilder(
        extensions=extensions,
        ignore_patterns=effective_ignore,
        include_paths=include,
        conventional_entries=conventional_entries,
    )
    records = graph.build(root_dir, entry)

    report = AnalysisReport(root_dir=root_dir)
    report.entry_points = [
        r.module_name for r in records if r.is_entry
    ]
    report.summary.total_files = len(records)
    report.summary.reachable_files = sum(1 for r in records if r.reachable)
    report.modules = records

    if detect_cycles:
        report.cycles = graph.detect_cycles(records)

    hooks = hooks or default_hooks()
    enabled_rules = set(rules) if rules else set(hooks.keys())

    tree_map = {r.path: tree for r in records if (tree := graph.tree_for(r.path)) is not None}

    options = {
        "include_entry_exports": include_entry_exports,
        "conventional_entries": conventional_entries,
        "detect_cycles": detect_cycles,
    }

    for rule, cls in hooks.items():
        if rule not in enabled_rules:
            continue
        finder = cls(report, graph=graph, trees=tree_map, options=options)
        finder.run(records)

    return report