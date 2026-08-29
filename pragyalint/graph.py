"""Build a module graph from Python source using the standard library `ast` module."""

from __future__ import annotations

import ast
import os
import re
from typing import Dict, List, Optional, Set, Tuple

from pragyalint.models import ImportRecord, ModuleRecord

_DYNAMIC_IMPORT_PATTERN = re.compile(
    r"(?:importlib\s*\.\s*(?:import_module|__import__)|__import__)\s*\(\s*"
)


class ParseError(Exception):
    """Raised when a module cannot be parsed."""


class ModuleGraphBuilder:
    """Discover, parse, and link Python modules, then compute reachability."""

    def __init__(
        self,
        extensions: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
    ) -> None:
        self.extensions = extensions or [".py"]
        self.ignore_patterns = ignore_patterns or []
        self.include_paths = include_paths or []
        self._ignored_re = [
            re.compile(p if p.startswith("^") else f"(^|/){p}($|/)")
            for p in self.ignore_patterns
        ]

    # ------------------------------------------------------------------ #
    # Discovery
    # ------------------------------------------------------------------ #
    def discover(self, root_dir: str) -> List[str]:
        """Return the list of files to analyze under `root_dir`."""
        files: List[str] = []
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [
                d
                for d in dirnames
                if not self._is_ignored(os.path.join(dirpath, d))
                and not d.startswith(".")  # skip hidden dirs (.git, .venv, etc.)
                and d not in {"__pycache__", "node_modules", "site-packages", ".venv", "venv"}
            ]
            for filename in sorted(filenames):
                full = os.path.join(dirpath, filename)
                if self._should_include(full):
                    files.append(full)
        files.sort()
        return files

    def _should_include(self, path: str) -> bool:
        if self._is_ignored(path):
            return False
        _, ext = os.path.splitext(path)
        if ext not in self.extensions:
            return False
        if not self.include_paths:
            return True
        for inc in self.include_paths:
            pat = inc if inc.startswith("/") else f"/{inc}"
            if pat in "/" + path.replace(os.sep, "/"):
                return True
        return False

    def _is_ignored(self, path: str) -> bool:
        norm = path.replace(os.sep, "/")
        for pattern in self._ignored_re:
            if pattern.search(norm):
                return True
        return False

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #
    def parse(self, path: str) -> ast.Module:
        try:
            source = open(path, "r", encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            raise ParseError(f"cannot read {path}")
        try:
            return ast.parse(source, filename=path)
        except SyntaxError as exc:
            raise ParseError(f"cannot parse {path}: {exc}")
        except ValueError as exc:
            raise ParseError(f"cannot parse {path}: {exc}")

    def module_name_for(self, root_dir: str, path: str) -> str:
        """Derive a dotted module name for `path` relative to `root_dir`."""
        rel = os.path.relpath(path, root_dir)
        parts = rel.replace(os.sep, "/").split("/")
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            last = parts[-1]
            if last.endswith(".py"):
                last = last[:-3]
            parts = parts[:-1] + [last]
        return ".".join(parts)

    # ------------------------------------------------------------------ #
    # Extract imports / exports
    # ------------------------------------------------------------------ #
    def extract_imports(self, tree: ast.Module, module_name: str) -> List[ImportRecord]:
        imports: List[ImportRecord] = []
        package_root = module_name.split(".")[:-1]

        def resolve(dotted: str) -> str:
            """Combine the dotted import name with the module's package root."""
            return ".".join(package_root) + ("." if package_root else "") + dotted

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportRecord(module=resolve(alias.name), names=[alias.asname or alias.name])
                    )
            elif isinstance(node, ast.ImportFrom):
                level = node.level
                base = node.module or ""
                if level > 0:
                    # relative import
                    depth_base = package_root[: len(package_root) - (level - 1)]
                    target = ".".join(depth_base + ([base] if base else []))
                else:
                    target = base
                names = [
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name != "*"
                ]
                imports.append(ImportRecord(module=target, names=names))
            elif isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "importlib"
                    and func.attr in {"import_module", "__import__"}
                ) or (isinstance(func, ast.Name) and func.id == "__import__"):
                    if node.args and isinstance(node.args[0], ast.Constant):
                        target = node.args[0].value
                        imports.append(
                            ImportRecord(
                                module=resolve(target) if not target.startswith(".") else target,
                                is_dynamic=True,
                            )
                        )
        return imports

    def extract_exports(self, tree: ast.Module) -> List[str]:
        """Collect top-level public names defined in the module.

        Names brought in via ``import``/``from ... import`` are handled by the
        re-export / unused-import analysis and are intentionally excluded here so
        that only *definitions* are treated as exports.
        """
        exports: Set[str] = set()
        explicit = None
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    exports.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            explicit = {
                                elt.value
                                for elt in node.value.elts
                                if isinstance(elt, ast.Constant)
                            }
                    elif isinstance(target, ast.Name) and not target.id.startswith("_"):
                        exports.add(target.id)
                    elif isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name) and not elt.id.startswith("_"):
                                exports.add(elt.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
                    exports.add(node.target.id)
        if explicit is not None:
            return sorted(explicit)
        return sorted(exports)

    # ------------------------------------------------------------------ #
    # Build + analyze
    # ------------------------------------------------------------------ #
    def build(self, root_dir: str, entry_points: List[str]) -> List[ModuleRecord]:
        files = self.discover(root_dir)
        records: List[ModuleRecord] = []
        by_name: Dict[str, ModuleRecord] = {}

        file_to_name = {}
        for path in files:
            tree = self.parse(path)
            module_name = self.module_name_for(root_dir, path)
            record = ModuleRecord(
                path=path,
                module_name=module_name,
                is_package=os.path.basename(path) == "__init__.py",
                is_entry=PathIsEntry(path, module_name, entry_points, root_dir),
                imports=self.extract_imports(tree, module_name),
                exports=self.extract_exports(tree),
            )
            records.append(record)
            by_name[module_name] = record
            file_to_name[os.path.abspath(path)] = module_name

        # Keep a private tree reference for finders that need it.
        self._trees: Dict[str, ast.Module] = {}
        for path in files:
            self._trees[os.path.abspath(path)] = self.parse(path)

        self._module_names = set(by_name.keys())
        self._by_name = by_name

        # resolve import targets to module records
        for record in records:
            new_imports: List[ImportRecord] = []
            for imp in record.imports:
                target_name = self._resolve_import_name(imp)
                imp._to = by_name.get(target_name)  # type: ignore[attr-defined]
                imp._target_name = target_name  # type: ignore[attr-defined]
                new_imports.append(imp)
                # `from pkg import helper` also reaches the submodule helper
                for name in imp.names:
                    sub = ".".join([target_name, name]) if target_name else name
                    if sub in self._module_names and sub != target_name:
                        extra = ImportRecord(module=sub, names=[])
                        extra._to = by_name.get(sub)  # type: ignore[attr-defined]
                        extra._target_name = sub  # type: ignore[attr-defined]
                        new_imports.append(extra)
            record.imports = new_imports

        self._compute_reachability(records)
        self._compute_used_members()
        return records

    def resolve_to_record(self, module_name: str) -> Optional[ModuleRecord]:
        """Public helper: map an import target name to a known module record."""
        return getattr(self, "_by_name", {}).get(module_name)

    def _compute_used_members(self) -> None:
        """Compute the set of (module_name, member_name) pairs accessed across the
        project via qualified access like ``alias.member`` (e.g. ``helper.used``).

        Populates ``self.used_members`` and ``self.module_aliases`` (per-file map of
        imported module *alias* -> module name) for finders to consume.
        """
        used_members: Set[Tuple[str, str]] = set()
        module_aliases: Dict[str, Dict[str, str]] = {}
        for record in self._by_name.values():
            tree = self._trees.get(os.path.abspath(record.path))
            aliases: Dict[str, str] = {}
            if tree is not None:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            bound = alias.asname or alias.name.split(".")[0]
                            aliases[bound] = alias.name
                    elif isinstance(node, ast.ImportFrom):
                        base = node.module or ""
                        for alias in node.names:
                            if alias.name == "*":
                                continue
                            bound = alias.asname or alias.name
                            # `from pkg import helper` gives alias `helper` of module pkg.helper
                            if (base + "." + alias.name) in self._module_names:
                                aliases[bound] = base + "." + alias.name
                    elif isinstance(node, ast.Call):
                        # __import__("x") / importlib.import_module("x")
                        pass
                for node in ast.walk(tree):
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                        alias = node.value.id
                        module = aliases.get(alias)
                        if module:
                            used_members.add((module, node.attr))
            module_aliases[record.module_name] = aliases
        self.used_members = used_members
        self.module_aliases = module_aliases

    def used_members_for(self, module_name: str) -> Set[str]:
        """Public helper: members of ``module_name`` that are accessed via
        ``alias.member`` anywhere in the project (may be None for empty)."""
        seen: Set[str] = set()
        for key in getattr(self, "used_members", set()):
            if key[0] == module_name:
                seen.add(key[1])
        return seen

    def tree_for(self, path: str) -> Optional[ast.Module]:
        return getattr(self, "_trees", {}).get(os.path.abspath(path))

    def _resolve_import_name(self, imp: ImportRecord) -> str:
        # Try progressively shorter prefixes until one matches a known module.
        parts = imp.module.split(".")
        for i in range(len(parts), 0, -1):
            cand = ".".join(parts[:i])
            if cand in self._module_names:
                return cand
        return imp.module

    def _compute_reachability(self, records: List[ModuleRecord]) -> None:
        by_name = self._by_name
        names: Set[str] = set()
        for record in records:
            if record.is_entry:
                names.add(record.module_name)

        stack = list(names)
        visited: Set[str] = set()
        while stack:
            name = stack.pop()
            if name in visited:
                continue
            visited.add(name)
            record = by_name.get(name)
            if record is None:
                continue
            for imp in record.imports:
                target = imp._to  # type: ignore[attr-defined]
                if target is not None and not target.reachable:
                    target.reachable = True
                    stack.append(target.module_name)

        for record in records:
            record.reachable = record.reachable or record.module_name in visited

    def detect_cycles(self, records: List[ModuleRecord]) -> List[List[str]]:
        """Return strongly connected components with >1 member or self-imports."""
        by_name = {r.module_name: r for r in records}
        index = {}
        lowlink = {}
        on_stack = set()
        stack = []
        cycles: List[List[str]] = []
        counter = [0]

        for name in by_name:
            if name not in index:
                self._strongconnect(
                    name, by_name, index, lowlink, on_stack, stack, cycles, counter
                )
        return cycles

    def _strongconnect(
        self, name, by_name, index, lowlink, on_stack, stack, cycles, counter
    ):
        index[name] = counter[0]
        lowlink[name] = counter[0]
        counter[0] += 1
        stack.append(name)
        on_stack.add(name)

        record = by_name.get(name)
        if record is not None:
            for imp in record.imports:
                target_name = imp._target_name  # type: ignore[attr-defined]
                if target_name not in by_name:
                    continue
                if target_name not in index:
                    self._strongconnect(
                        target_name, by_name, index, lowlink, on_stack, stack, cycles, counter
                    )
                    lowlink[name] = min(lowlink[name], lowlink[target_name])
                elif target_name in on_stack:
                    lowlink[name] = min(lowlink[name], index[target_name])
                elif target_name == name:
                    # self import edge
                    lowlink[name] = min(lowlink[name], index[target_name])

        if lowlink[name] == index[name]:
            component = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                component.append(w)
                if w == name:
                    break
            if len(component) > 1:
                cycles.append(component)


def PathIsEntry(path: str, module_name: str, entry_points: List[str], root_dir: str) -> bool:
    """Determine whether a module qualifies as an analysis entry point."""
    if not entry_points:
        # conventional entries
        if path.endswith(os.path.join("__main__.py")):
            return True
        normalized = os.path.basename(path)
        if normalized in {"main.py", "app.py", "cli.py", "setup.py"}:
            return True
        if os.path.basename(path) == "__init__.py" and os.path.dirname(path) == root_dir:
            return True
        return False
    for ep in entry_points:
        if ep == module_name:
            return True
        if os.path.abspath(ep) == os.path.abspath(path):
            return True
        if ep.endswith(".py") and os.path.abspath(ep) == os.path.abspath(path):
            return True
        if ep == "/" + path.replace(os.sep, "/") or module_name.endswith(ep):
            return True
    return False
