"""Find public names that are never imported by other modules."""

from __future__ import annotations

import ast
from typing import Dict, List, Set

from pragyalint.models import Confidence, Finding, ModuleRecord
from pragyalint.finders import Finder


class UnusedExportsFinder(Finder):
    """Report exported names that no other module ever imports/references.

    A name is considered used when another module imports it (via ``from x
    import name``, ``import x`` followed by ``x.name`` usage, or ``__all__``
    re-exports) or when it is consumed by a dynamic import.
    """

    rule = "unused_export"

    def run(self, records: List[ModuleRecord]) -> None:
        # name -> set of modules that import/reference it
        importers: Dict[str, int] = {}
        # names used dynamically anywhere in the project
        dynamic_names: Set[str] = set()

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

        for record in records:
            if not record.reachable:
                # file-level finding already covers unreachable modules
                continue
            if record.is_entry and not self.options.get("include_entry_exports", False):
                # entry files' own exports form the public surface; only flag
                # them as unused when explicitly requested.
                continue
            member_used = self.graph.used_members_for(record.module_name) if self.graph else set()
            for export in record.exports:
                key = (record.module_name, export)
                if importers.get(key, 0) > 0:
                    continue
                if export in member_used:
                    continue
                if export in dynamic_names:
                    continue
                self.emit(
                    Finding(
                        rule=self.rule,
                        confidence=Confidence.MEDIUM,
                        message=(
                            f"export {export!r} of module {record.module_name!r} "
                            f"is never imported"
                        ),
                        file=record.path,
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
