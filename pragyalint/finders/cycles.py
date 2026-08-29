"""Report circular import cycles between modules."""

from __future__ import annotations

from typing import List

from pragyalint.models import Confidence, Finding, ModuleRecord
from pragyalint.finders import Finder


class CycleFinder(Finder):
    """Emit a finding for each detected import cycle."""

    rule = "cycle"

    def run(self, records: List[ModuleRecord]) -> None:
        if not self.report.cycles:
            return
        for component in self.report.cycles:
            self.emit(
                Finding(
                    rule=self.rule,
                    confidence=Confidence.LOW,
                    message="circular import cycle: " + " -> ".join(component),
                    extra={"cycle": component},
                )
            )
