"""Core data model: confidence levels, findings, module records, and the report."""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional


class Confidence:
    """Confidence levels for findings."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    ORDER = [HIGH, MEDIUM, LOW]

    @classmethod
    def parse(cls, value: str) -> str:
        v = value.strip().lower()
        if v in cls.ORDER:
            return v
        raise ValueError(f"unknown confidence level: {value!r}")

    @classmethod
    def parse_min(cls, value: str) -> int:
        """Map a --fail-on / --confidence threshold to an index in ORDER."""
        v = value.strip().lower()
        if v == "none":
            return -1
        if v.endswith("+"):
            return cls.ORDER.index(cls.parse(v[:-1]))
        return cls.ORDER.index(cls.parse(v))


@dataclasses.dataclass
class Finding:
    """A single dead-code finding."""

    rule: str
    confidence: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "confidence": self.confidence,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "extra": self.extra or {},
        }


@dataclasses.dataclass
class ImportRecord:
    """A resolved import between modules."""

    module: str
    names: List[str] = dataclasses.field(default_factory=list)
    is_dynamic: bool = False
    is_conditional: bool = False
    optional: bool = False


@dataclasses.dataclass
class ModuleRecord:
    """Metadata about a single analyzed module."""

    path: str  # filesystem path
    module_name: str  # dotted import name
    is_package: bool = False
    is_entry: bool = False
    exports: List[str] = dataclasses.field(default_factory=list)
    imports: List[ImportRecord] = dataclasses.field(default_factory=list)
    reachable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "module_name": self.module_name,
            "is_package": self.is_package,
            "is_entry": self.is_entry,
            "exports": self.exports,
            "reachable": self.reachable,
            "imports": [
                {
                    "module": imp.module,
                    "names": imp.names,
                    "is_dynamic": imp.is_dynamic,
                    "is_conditional": imp.is_conditional,
                    "optional": imp.optional,
                }
                for imp in self.imports
            ],
        }


@dataclasses.dataclass
class Summary:
    """Summary counts for the analysis report."""

    total_files: int = 0
    reachable_files: int = 0
    findings: int = 0
    by_rule: Dict[str, int] = dataclasses.field(default_factory=dict)
    by_confidence: Dict[str, int] = dataclasses.field(default_factory=dict)

    def add(self, finding: Finding) -> None:
        self.findings += 1
        self.by_rule[finding.rule] = self.by_rule.get(finding.rule, 0) + 1
        self.by_confidence[finding.confidence] = (
            self.by_confidence.get(finding.confidence, 0) + 1
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "reachable_files": self.reachable_files,
            "findings": self.findings,
            "by_rule": self.by_rule,
            "by_confidence": self.by_confidence,
        }


@dataclasses.dataclass
class AnalysisReport:
    """Full result of an analysis."""

    root_dir: str
    summary: Summary = dataclasses.field(default_factory=Summary)
    findings: List[Finding] = dataclasses.field(default_factory=list)
    modules: List[ModuleRecord] = dataclasses.field(default_factory=list)
    entry_points: List[str] = dataclasses.field(default_factory=list)
    cycles: List[List[str]] = dataclasses.field(default_factory=list)
    deps: Dict[str, Dict[str, Any]] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_dir": self.root_dir,
            "summary": self.summary.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "modules": [m.to_dict() for m in self.modules],
            "entry_points": self.entry_points,
            "cycles": self.cycles,
            "deps": self.deps,
        }


def should_fail(report: AnalysisReport, min_confidence: int) -> bool:
    """Return True when the report contains findings at/above the threshold."""
    for finding in report.findings:
        idx = Confidence.ORDER.index(finding.confidence)
        if idx <= min_confidence:
            return True
    return False
