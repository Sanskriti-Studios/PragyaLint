"""Find public names that are never imported by other modules."""

from __future__ import annotations

import ast
from typing import Dict, List, Set

from pragyalint.models import Confidence, Finding, ModuleRecord
from pragyalint.finders import Finder
from pragyalint.dynamic import (
    collect_dispatch_table_names,
    collect_getattr_literal_names,
    has_dynamic_dispatch,
    has_keep_pragma,
    read_source_lines,
)


class UnusedExportsFinder(Finder):
    """Report exported names that no other module ever imports/references.

    A name is considered used when another module imports it (via ``from x
    import name``, ``import x`` followed by ``x.name`` usage, or ``__all__``
    re-exports), when it is consumed by a dynamic import, when it's used as
    the value in a dict/list/tuple/set literal (a command-dispatch table),
    or when it's marked with a ``# pragyalint: keep`` comment. When a module
    uses ``exec``/``eval``/``getattr``/``globals()`` -- patterns that can
    hide real usage from static analysis entirely -- remaining findings in
    that module are reported at LOW confidence rather than MEDIUM, since
    reachability can't be trusted there.
    """

    rule = "unused_export"

    def run(self, records: List[ModuleRecord]) -> None:
        # name -> set of modules that import/reference it
        importers: Dict[str, int] = {}
        # names used dynamically anywhere in the project
        dynamic_names: Set[str] = set()
        # Whether *any* module in the project uses exec/eval/getattr/globals.
        # Project-wide, not per-file -- see unused_local.py for why.
        project_is_dynamic = False

        tree_map: Dict[str, ast.Module] = self.trees

        for record in records:
            for imp in record.imports:
                target_module = getattr(imp, "_target_name", None)
                if target_module is None:
                    continue
                for name in imp.names:
                    key = (target_module, name)
                    importers[key] = importers.get(key, 0) + 1

        for record in records:
            tree = tree_map.get(record.path)
            if tree is None:
                continue
            for name, usage in _collect_member_usage(tree):
                if name:
                    dynamic_names.add(name if not isinstance(name, tuple) else name[1])
            dynamic_names |= collect_dispatch_table_names(tree)
            dynamic_names |= collect_getattr_literal_names(tree)
            if has_dynamic_dispatch(tree):
                project_is_dynamic = True

        for record in records:
            if not record.reachable:
                # file-level finding already covers unreachable modules
                continue
            if record.is_entry and not self.options.get("include_entry_exports", False):
                # entry files' own exports form the public surface; only flag
                # them as unused when explicitly requested.
                continue
            member_used = self.graph.used_members_for(record.module_name) if self.graph else set()
            source_lines = read_source_lines(record.path)
            tree = tree_map.get(record.path)
            def_lines = _export_def_lines(tree) if tree is not None else {}
            for export in record.exports:
                key = (record.module_name, export)
                if importers.get(key, 0) > 0:
                    continue
                if export in member_used:
                    continue
                if export in dynamic_names:
                    continue
                if has_keep_pragma(source_lines, def_lines.get(export)):
                    continue
                confidence = Confidence.LOW if project_is_dynamic else Confidence.MEDIUM
                message = (
                    f"export {export!r} of module {record.module_name!r} "
                    f"is never imported"
                )
                if project_is_dynamic:
                    message += (
                        " (project uses exec/eval/getattr/globals somewhere "
                        "-- this may be a dynamic-dispatch false positive; "
                        "review before deleting)"
                    )
                self.emit(
                    Finding(
                        rule=self.rule,
                        confidence=confidence,
                        message=message,
                        file=record.path,
                        line=def_lines.get(export),
                        extra={"module": record.module_name, "name": export},
                    )
                )


def _collect_member_usage(tree: ast.Module) -> List[tuple]:
    """Collect Attribute names like ``module.name`` used dynamically."""
    usages: List[tuple] = []
    # module names imported in this file
    module_alias: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_alias.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            pass
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in module_alias:
                usages.append((node.value.id, node.attr))
    return usages


def _export_def_lines(tree: ast.Module) -> Dict[str, int]:
    """Map top-level def/class/assignment names to their source line, so
    findings and pragma checks can point at the right line.
    """
    lines: Dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            lines[node.name] = node.lineno
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lines[target.id] = node.lineno
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                lines[node.target.id] = node.lineno
    return lines