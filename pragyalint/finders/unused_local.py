"""Find module-level definitions that are referenced nowhere in the project."""

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

_CONTAINER_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


class UnusedLocalFinder(Finder):
    """Report top-level functions, classes, and variables that are defined but
    referenced by no reachable module (including their own module).

    Names re-exported through ``__all__`` or imported by other modules are kept.
    Names only ever looked up dynamically (dispatch tables, ``getattr``,
    ``globals()``, ``exec``/``eval``, or marked with a ``# pragyalint: keep``
    comment) are also kept, or reported at LOW confidence when the dynamic
    pattern can't be resolved statically -- static analysis can't prove those
    are dead, so they should never be auto-deleted.
    """

    rule = "unused_local"

    def run(self, records: List[ModuleRecord]) -> None:
        # Build a global read-count map: name -> count of read references.
        # Qualified attribute uses (obj.attr) are excluded so that only plain
        # name references count as "use" of the definition.
        read_counts: Dict[str, int] = {}

        tree_map: Dict[str, ast.Module] = self.trees

        # Names referenced anywhere as the *value* of a dict/list/tuple/set
        # literal -- the shape of a command-dispatch table -- are treated as
        # used project-wide, since they're never called by a bare name.
        dispatch_names: Set[str] = set()
        # Whether *any* module in the project uses exec/eval/getattr/globals.
        # This has to be project-wide, not per-file: a reflective call in
        # app.py can just as easily name a function defined in runtime.py --
        # the risk isn't confined to the file containing the getattr() call.
        project_is_dynamic = False

        for record in records:
            tree = tree_map.get(record.path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    read_counts[node.id] = read_counts.get(node.id, 0) + 1
            dispatch_names |= collect_dispatch_table_names(tree)
            dispatch_names |= collect_getattr_literal_names(tree)
            if has_dynamic_dispatch(tree):
                project_is_dynamic = True

        # Names referenced by another module's import are "used" globally.
        for record in records:
            for imp in record.imports:
                for name in imp.names:
                    read_counts[name] = read_counts.get(name, 0) + 1

        for record in records:
            if not record.reachable:
                continue
            if record.is_entry and not self.options.get("include_entry_exports", False):
                # Entry files (conventional entry points, and conventional
                # test files like test_*.py/conftest.py) are invoked from
                # outside the import graph -- by the interpreter, or by
                # pytest's own name-based collection. Their top-level
                # definitions are the public surface pytest/the runtime
                # calls into, not dead code, so treat them the same way
                # unused_exports already treats entry-file exports.
                continue
            tree = tree_map.get(record.path)
            if tree is None:
                continue
            member_used = self.graph.used_members_for(record.module_name) if self.graph else set()
            source_lines = read_source_lines(record.path)
            for node in tree.body:
                if isinstance(node, _CONTAINER_TYPES):
                    if node.name.startswith("_"):
                        continue
                    if read_counts.get(node.name, 0) > 0:
                        continue
                    if node.name in member_used:
                        continue
                    if node.name in dispatch_names:
                        continue
                    if has_keep_pragma(source_lines, getattr(node, "lineno", None)):
                        continue
                    confidence = Confidence.LOW if project_is_dynamic else Confidence.MEDIUM
                    message = (
                        f"{type(node).__name__} {node.name!r} is defined "
                        f"but never used"
                    )
                    if project_is_dynamic:
                        message += (
                            " (project uses exec/eval/getattr/globals "
                            "somewhere -- this may be a dynamic-dispatch "
                            "false positive; review before deleting)"
                        )
                    self.emit(
                        Finding(
                            rule=self.rule,
                            confidence=confidence,
                            message=message,
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
                        if name in dispatch_names:
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