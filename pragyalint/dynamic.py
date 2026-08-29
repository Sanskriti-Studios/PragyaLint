"""Heuristics for dynamic-usage patterns that static AST analysis can't see.

Interpreters, plugin systems, and command-dispatch code frequently invoke a
function by name rather than by a plain identifier reference: via
``getattr(module, name)``, ``globals()[name]``, ``exec``/``eval``, or a
dict/list literal that maps strings (or registers callables) to functions.
None of these show up as an ``ast.Name`` load, so the dead-code finders can
mistake a live, reflectively-called function for dead code. This module
centralizes the heuristics used to avoid that class of false positive.
"""

from __future__ import annotations

import ast
from typing import List, Set

PRAGMA = "pragyalint: keep"


def has_dynamic_dispatch(tree: ast.Module) -> bool:
    """Return True if the module contains patterns that can hide real uses
    of a top-level name from static analysis: ``exec``/``eval`` calls,
    ``getattr(obj, non_literal_name)``, or ``globals()``/``locals()``
    access. When True, callers should treat "unused" findings in this module
    as low-confidence rather than deleting anything automatically.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name in ("exec", "eval"):
                return True
            if name == "getattr" and len(node.args) >= 2:
                attr_arg = node.args[1]
                if not (isinstance(attr_arg, ast.Constant) and isinstance(attr_arg.value, str)):
                    return True
            if name in ("globals", "locals"):
                return True
    return False


def collect_getattr_literal_names(tree: ast.Module) -> Set[str]:
    """Collect names passed as string-literal attributes to ``getattr``,
    e.g. ``getattr(runtime, "execute_line")``. This is resolvable -- we know
    exactly which name it reaches -- but it still isn't an ``ast.Attribute``
    node, so the plain ``module.attr`` usage tracker misses it. Treat it the
    same as a real attribute access.
    """
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "getattr" and len(node.args) >= 2:
                attr_arg = node.args[1]
                if isinstance(attr_arg, ast.Constant) and isinstance(attr_arg.value, str):
                    names.add(attr_arg.value)
    return names


def collect_dispatch_table_names(tree: ast.Module) -> Set[str]:
    """Collect bare names used as *values* inside dict/list/tuple/set
    literals, e.g. ``{"echo": execute_line}`` or ``HANDLERS = [run_block,
    execute_line]``. These are the classic shape of a command-dispatch
    table: the function is never called by its plain name, only looked up
    through the table, so a naive Name-load count misses it entirely.
    """
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for value in node.values:
                if isinstance(value, ast.Name):
                    names.add(value.id)
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for elt in node.elts:
                if isinstance(elt, ast.Name):
                    names.add(elt.id)
    return names


def has_keep_pragma(source_lines: List[str], lineno: "int | None") -> bool:
    """Check for a ``# pragyalint: keep`` comment on the definition's own
    line or the line directly above it, so a function/class/variable can be
    explicitly exempted from unused_local/unused_export findings.
    """
    if not lineno:
        return False
    for candidate in (lineno, lineno - 1):
        if 1 <= candidate <= len(source_lines):
            if PRAGMA in source_lines[candidate - 1]:
                return True
    return False


def read_source_lines(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return []