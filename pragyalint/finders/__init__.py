"""Finder base types."""

from __future__ import annotations

from typing import Dict, List, Optional

from pragyalint.models import AnalysisReport, Finding, ModuleRecord


class Finder:
    """Base class for a dead-code detection pass.

    Subclasses implement ``run`` and emit Findings into the report.
    """

    rule = "generic"

    def __init__(
        self,
        report: AnalysisReport,
        graph: Optional[object] = None,
        trees: Optional[Dict[str, object]] = None,
        options: Optional[dict] = None,
    ) -> None:
        self.report = report
        self.graph = graph
        self.trees = trees or {}
        self.options = options or {}

    def emit(self, finding: Finding) -> None:
        self.report.findings.append(finding)
        self.report.summary.add(finding)

    def run(self, records: List[ModuleRecord]) -> None:
        raise NotImplementedError


__all__ = ["Finder"]
