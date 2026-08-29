"""Find module-level definitions that are referenced nowhere in the project."""

from __future__ import annotations

import ast
from typing import Dict, List

from pragyalint.models import Confidence, Finding, ModuleRecord
from pragyalint.finders import Finder

_CONTAINER_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


class UnusedLocalFinder(Finder):
    """Report top-level functions, classes, and variables that are defined but
    referenced by no reachable module (including their own module).

    Names re-exported through ``__all__`` or imported by other modules are kept.
    """

    rule = "unused_local"

    def run(self, records: List[ModuleRecord]) -> None:
        # Build a global read-count map: name -> count of read references.
        # Qualified attribute uses (obj.attr) are excluded so that only plain
        # name references count as "use" of the definition.
        read_counts: Dict[str, int] = {}

        tree_map: Dict[str, ast.Module] = self.trees

        for record in records:
            tree = tree_map.get(record.path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    read_counts[node.id] = read_counts.get(node.id, 0) + 1

        # Names referenced by another module's import are "used" globally.
        for record in records:
            for imp in record.imports:
                for name in imp.names:
                    read_counts[name] = read_counts.get(name, 0) + 1

        for record in records:
            if not record.reachable:
                continue
            tree = tree_map.get(record.path)
            if tree is None:
                continue
            member_used = self.graph.used_members_for(record.module_name) if self.graph else set()
            for node in tree.body:
                if isinstance(node, _CONTAINER_TYPES):
                    if node.name.startswith("_"):
                        continue
                    if read_counts.get(node.name, 0) > 0:
                        continue
                    if node.name in member_used:
                        continue
                    self.emit(
                        Finding(
                            rule=self.rule,
                            confidence=Confidence.MEDIUM,
                            message=(
                                f"{type(node).__name__} {node.name!r} is defined "
                                f"but never used"
                            ),
                            file=record.path,
                            line=getattr(node, "lineno", None),
                            column=getattr(node, "col_offset", None),
                            extra={"name": node.name, "kind": type(node).__name__},
                        )
                    )
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = _assignment_targets(node)
                    for name in targets:
                        if name.startswith("_") or name == "__all__":
                            continue
                        # module-level constants are often consumed externally;
                        # keep a low-confidence warning only for obvious dead sets
                        if read_counts.get(name, 0) > 0:
                            continue
                        if isinstance(node, ast.Assign) and _is_constant(node.value):
                            self.emit(
                                Finding(
                                    rule=self.rule,
                                    confidence=Confidence.LOW,
                                    message=f"variable {name!r} is assigned but never used",
                                    file=record.path,
                                    line=getattr(node, "lineno", None),
                                    column=getattr(node, "col_offset", None),
                                    extra={"name": name, "kind": "variable"},
                                )
                            )


def _assignment_targets(node) -> List[str]:
    names: List[str] = []
    if isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            names.append(node.target.id)
        return names
    for target in node.targets:
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
            for elt in target.elts:
                if isinstance(elt, ast.Name):
                    names.append(elt.id)
    return names


def _is_constant(value: ast.AST) -> bool:
    return isinstance(value, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set))
