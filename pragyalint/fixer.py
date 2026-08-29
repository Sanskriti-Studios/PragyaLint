"""Opt-in confidence-gated fixing of dead code.

Mimics OptiPrune's ``--fix`` model: reports are produced by the analyzer, and
fixes are applied *explicitly* via a separate pass. Every fix is confidence
gated and supports dry runs.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Set, Tuple

from pragyalint.models import AnalysisReport, Confidence, Finding


class FixResult:
    """Result of applying fixes: what was changed, planned, or skipped."""

    def __init__(self) -> None:
        self.applied: List[str] = []
        self.dry_run: List[str] = []
        self.skipped: List[str] = []

    def record(self, action: str, dry_run: bool) -> None:
        if dry_run:
            self.dry_run.append(action)
        else:
            self.applied.append(action)

    def to_dict(self) -> dict:
        return {
            "applied": self.applied,
            "dry_run": self.dry_run,
            "skipped": self.skipped,
        }


def apply_fixes(
    report: AnalysisReport,
    targets: List[str],
    min_confidence: str = "high",
    dry_run: bool = False,
    force: bool = False,
) -> FixResult:
    """Apply fixes for the requested targets.

    ``targets`` is a subset of: ``files``, ``imports``, ``exports``.
    Returns a :class:`FixResult` describing changes.
    """
    result = FixResult()
    threshold = Confidence.ORDER.index(Confidence.parse(min_confidence))

    by_rule = _findings_by_rule(report)

    if "files" in targets:
        _fix_unreachable_files(report, result, threshold, dry_run, force, by_rule)

    if "imports" in targets:
        _fix_unused_imports(report, result, threshold, dry_run, force, by_rule)

    if "exports" in targets:
        _fix_unused_exports(report, result, threshold, dry_run, force, by_rule)

    return result


def _findings_by_rule(report: AnalysisReport) -> Dict[str, List[Finding]]:
    grouped: Dict[str, List[Finding]] = {}
    for finding in report.findings:
        grouped.setdefault(finding.rule, []).append(finding)
    return grouped


def _confidence_at_or_above(confidence: str, threshold: int) -> bool:
    idx = Confidence.ORDER.index(confidence)
    return idx <= threshold  # lower index == higher confidence


def _fix_unreachable_files(
    report: AnalysisReport,
    result: FixResult,
    threshold: int,
    dry_run: bool,
    force: bool,
    by_rule: Dict[str, List[Finding]],
) -> None:
    # never delete anything that is a package __init__ or an entry point
    for record in report.modules:
        if record.reachable or record.is_package or record.is_entry:
            continue
        finding = _first_finding(by_rule.get("unused_file", []), record.path)
        if finding is None or not _confidence_at_or_above(finding.confidence, threshold):
            continue
        action = f"delete {record.path}"
        if dry_run:
            result.dry_run.append(action)
        else:
            try:
                os.remove(record.path)
                result.applied.append(action)
            except OSError as exc:
                result.skipped.append(f"{action} ({exc})")


def _fix_unused_imports(
    report: AnalysisReport,
    result: FixResult,
    threshold: int,
    dry_run: bool,
    force: bool,
    by_rule: Dict[str, List[Finding]],
) -> None:
    findings = [f for f in by_rule.get("unused_import", []) if f.file]
    grouped: Dict[str, List[Finding]] = {}
    for finding in findings:
        grouped.setdefault(finding.file, []).append(finding)

    for path, fs in grouped.items():
        if not _confidence_at_or_above(min(f.confidence for f in fs), threshold):
            continue
        lines = _read_lines(path)
        if lines is None:
            continue
        import ast

        try:
            tree = ast.parse("".join(lines), filename=path)
        except SyntaxError:
            continue
        import_nodes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        # Group unused findings by the import statement they belong to.
        by_stmt: Dict[int, List[Finding]] = {}
        for finding in fs:
            stmt = _import_stmt_at_line(import_nodes, finding.line)
            if stmt is not None:
                by_stmt.setdefault(stmt.lineno, []).append(finding)

        removals: Dict[int, int] = {}  # whole-statement removals: start -> end
        rewrites: Dict[int, str] = {}  # partial rewrites: start line -> new text
        for start, stmt_findings in by_stmt.items():
            stmt = _import_stmt_at_line(import_nodes, start)
            if stmt is None:
                continue
            all_names = _statement_names(stmt)
            unused = {
                f.extra.get("name") or f.extra.get("import")
                for f in stmt_findings
            }
            used = all_names - unused
            if not used:
                # remove the whole statement
                removals[start] = getattr(stmt, "end_lineno", start)
            elif _is_from_import(stmt) and used:
                # rewrite the `from X import a, b` line to keep only used names
                new_text = _rewrite_from_import(stmt, used)
                if new_text:
                    rewrites[start] = new_text

        action = f"remove unused imports in {path}"
        if dry_run:
            result.dry_run.append(action)
        else:
            new_content = _apply_import_edits(lines, removals, rewrites)
            if _write_lines(path, new_content):
                result.applied.append(action)
            else:
                result.skipped.append(action)


def _fix_unused_exports(
    report: AnalysisReport,
    result: FixResult,
    threshold: int,
    dry_run: bool,
    force: bool,
    by_rule: Dict[str, List[Finding]],
) -> None:
    # Removing definitions is riskier (may be the public API surface). We only
    # attempt this for names that are *not* referenced by __all__ unless --force.
    findings = [f for f in by_rule.get("unused_export", []) if f.file]
    grouped: Dict[str, List[Finding]] = {}
    for finding in findings:
        grouped.setdefault(finding.file, []).append(finding)

    import ast

    for path, fs in grouped.items():
        if not _confidence_at_or_above(min(f.confidence for f in fs), threshold):
            continue
        lines = _read_lines(path)
        if lines is None:
            continue
        try:
            tree = ast.parse("".join(lines), filename=path)
        except SyntaxError:
            continue
        target_names = {f.extra.get("name") for f in fs}
        if not target_names:
            continue
        # skip names referenced by __all__
        if not force:
            all_names = _explicit_all_names(tree)
            target_names = target_names - all_names
            if not target_names:
                continue
        to_remove_linenos = _top_level_def_lines(tree, target_names)
        if not to_remove_linenos:
            continue
        action = f"remove unused definitions in {path}"
        if dry_run:
            result.dry_run.append(action)
        else:
            blocks = _line_blocks_to_remove(to_remove_linenos, len(lines))
            new_content = _delete_blocks(lines, blocks)
            if _write_lines(path, new_content):
                result.applied.append(action)
            else:
                result.skipped.append(action)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _read_lines(path: str) -> Optional[List[str]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read().splitlines(keepends=True)
    except (OSError, UnicodeDecodeError):
        return None


def _write_lines(path: str, lines: List[str]) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("".join(lines))
        return True
    except OSError:
        return False


def _first_finding(findings: List[Finding], path: str) -> Optional[Finding]:
    for finding in findings:
        if finding.file == path:
            return finding
    return None


def _import_stmt_at_line(nodes: List, line: int):
    for node in nodes:
        if node.lineno == line:
            return node
    return None


def _statement_names(stmt) -> Set[str]:
    import ast

    names: Set[str] = set()
    if isinstance(stmt, ast.Import):
        for alias in stmt.names:
            names.add(alias.asname or alias.name)
    elif isinstance(stmt, ast.ImportFrom):
        for alias in stmt.names:
            if alias.name != "*":
                names.add(alias.asname or alias.name)
    return names


def _explicit_all_names(tree) -> Set[str]:
    import ast

    names: Set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        names.update(
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                        )
    return names


def _top_level_def_lines(tree, target_names: Set[str]) -> Dict[int, int]:
    import ast

    result: Dict[int, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in target_names:
                result[node.lineno] = getattr(node, "end_lineno", node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in target_names:
                    result[node.lineno] = getattr(node, "end_lineno", node.lineno)
                    break
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id in target_names:
                result[node.lineno] = getattr(node, "end_lineno", node.lineno)
    return result


def _line_blocks_to_remove(
    start_to_end: Dict[int, int], total_lines: int
) -> List[Tuple[int, int]]:
    """Return (start_idx, end_idx) inclusive 0-based ranges of whole lines.

    ``start_to_end`` maps 1-based start lines to 1-based end lines so that
    multi-line statements (def bodies, multi-line imports) are removed fully.
    """
    ranges = []
    for start_1based, end_1based in start_to_end.items():
        s_idx = start_1based - 1
        e_idx = end_1based - 1
        if 0 <= s_idx < total_lines and s_idx <= e_idx:
            ranges.append((s_idx, e_idx))
    return ranges


def _is_from_import(stmt) -> bool:
    import ast

    return isinstance(stmt, ast.ImportFrom)


def _rewrite_from_import(stmt, used_names: Set[str]) -> Optional[str]:
    """Build a rewritten ``from X import ...`` statement keeping only used names.

    Preserves the original module, level (relative), and only keeps the used
    aliases (alias or its original name). Returns None if a rewrite is unsafe.
    """
    import ast

    kept = []
    for alias in stmt.names:
        if alias.name == "*":
            return None  # star imports are never partially rewritten
        name = alias.asname or alias.name
        if name not in used_names:
            continue
        if alias.asname:
            kept.append(f"{alias.name} as {alias.asname}")
        else:
            kept.append(alias.name)

    if not kept:
        return None

    prefix = "." * stmt.level
    module = stmt.module or ""
    mod = f"{prefix}{module}" if prefix else module
    indent = " " * stmt.col_offset
    return f"{indent}from {mod} import {', '.join(kept)}"


def _apply_import_edits(
    lines: List[str], removals: Dict[int, int], rewrites: Dict[int, str]
) -> List[str]:
    """Apply whole-statement removals and single-line rewrites to ``lines``.

    Returns new line list. Rewrites happen first (line numbers stable), then
    removals are applied from the bottom-up.
    """
    out = list(lines)
    # apply rewrites (no index change, single line each)
    for lineno, new_text in rewrites.items():
        idx = lineno - 1
        if 0 <= idx < len(out):
            out[idx] = new_text + "\n"

    # apply removals bottom-up to keep indexes valid
    for start, end in sorted(removals.items(), reverse=True):
        s_idx = start - 1
        e_idx = end - 1
        if 0 <= s_idx < len(out) and s_idx <= e_idx:
            del out[s_idx : e_idx + 1]
    return out


def _delete_blocks(lines: List[str], ranges: List[Tuple[int, int]]) -> List[str]:
    # Remove ranges from highest to lowest so indexes stay valid.
    result = list(lines)
    for start, end in sorted(ranges, reverse=True):
        del result[start : end + 1]
    return result
