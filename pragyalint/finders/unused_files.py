"""Find modules that are unreachable from any entry point."""

from __future__ import annotations

from typing import List

from pragyalint.models import Confidence, Finding, ModuleRecord
from pragyalint.finders import Finder


class UnusedFilesFinder(Finder):
    """Report modules that are not reachable from any entry point.

    To avoid false positives, modules whose names appear as the parent of
    any reachable/imported module are treated as package containers and kept.
    """

    rule = "unused_file"

    def run(self, records: List[ModuleRecord]) -> None:
        referenced_prefixes = set()
        module_names = {r.module_name for r in records}
        for record in records:
            for imp in record.imports:
                target = getattr(imp, "_target_name", None)
                if not target:
                    continue
                parts = target.split(".")
                for i in range(1, len(parts) + 1):
                    prefix = ".".join(parts[:i])
                    if prefix in module_names:
                        referenced_prefixes.add(prefix)

        for record in records:
            if record.reachable:
                continue
            if record.module_name in referenced_prefixes:
                # package __init__ that just contains reachable submodules
                if record.is_package:
                    continue
            self.emit(
                Finding(
                    rule=self.rule,
                    confidence=Confidence.HIGH,
                    message=(
                        f"module {record.module_name!r} is not reachable from any "
                        f"entry point"
                    ),
                    file=record.path,
                    extra={"module": record.module_name},
                )
            )
