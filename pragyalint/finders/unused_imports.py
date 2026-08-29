"""Find imports within a module that are never used in that module."""

from __future__ import annotations

import ast
from typing import List, Set

from pragyalint.models import Confidence, Finding, ModuleRecord
from pragyalint.finders import Finder


class UnusedImportsFinder(Finder):
    """Report ``import``/``from ... import`` statements whose bound names are
    never referenced in the importing module.

    This is a *local* check and ignores re-exported names (public API surface) and
    names consumed by ``__all__``.
    """

    rule = "unused_import"

    def run(self, records: List[ModuleRecord]) -> None:
        for record in records:
            tree = self.trees.get(record.path)
            if tree is None:
                continue
            used = _names_used(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        bound = alias.asname or alias.name.split(".")[0]
                        if bound in used:
                            continue
                        if _is_reexport(tree, bound):
                            continue
                        self.emit(
                            Finding(
                                rule=self.rule,
                                confidence=Confidence.HIGH,
                                message=f"import {alias.name!r} is never used",
                                file=record.path,
                                line=getattr(node, "lineno", None),
                                column=getattr(node, "col_offset", None),
                                extra={"import": alias.name, "name": bound},
                            )
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("__future__"):
                        continue
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        bound = alias.asname or alias.name
                        if bound in used:
                            continue
                        if _is_reexport(tree, bound):
                            continue
                        self.emit(
                            Finding(
                                rule=self.rule,
                                confidence=Confidence.HIGH,
                                message=(
                                    f"from {node.module or '.'} import {alias.name!r} "
                                    f"is never used"
                                ),
                                file=record.path,
                                line=getattr(node, "lineno", None),
                                column=getattr(node, "col_offset", None),
                                extra={
                                    "module": node.module,
                                    "import": alias.name,
                                    "name": bound,
                                },
                            )
                        )


def _names_used(tree: ast.Module) -> Set[str]:
    used: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            # skip the store context targets handled separately; a plain Name
            # read counts as usage.
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            pass
        elif isinstance(node, ast.arg):
            used.add(node.arg)
    # names that appear as a target of assignment do not count as usage of an
    # import unless read elsewhere; we already collected all Name reads.
    return used


def _is_reexport(tree: ast.Module, bound: str) -> bool:
    """Return True if `bound` is referenced by a module-level ``__all__``."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and elt.value == bound:
                                return True
    return False
