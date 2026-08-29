"""SARIF (Static Analysis Results Interchange Format) output.

Useful for CI systems like GitHub Code Scanning.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from pragyalint.models import AnalysisReport, Confidence

_LEVEL = {
    Confidence.HIGH: "error",
    Confidence.MEDIUM: "warning",
    Confidence.LOW: "note",
}

_RULES: Dict[str, Dict[str, str]] = {
    "unused_file": {"name": "unused-file", "shortDescription": "Unreferenced module"},
    "unused_export": {"name": "unused-export", "shortDescription": "Unused public export"},
    "unused_import": {"name": "unused-import", "shortDescription": "Unused import"},
    "unused_local": {"name": "unused-local", "shortDescription": "Unused definition"},
    "cycle": {"name": "cycle", "shortDescription": "Circular import cycle"},
}

_TOOL = {
    "driver": {
        "name": "PragyaLint",
        "informationUri": "https://github.com/example/pragyalint",
        "version": "0.1.0",
        "rules": [
            {
                "id": rule,
                "name": meta["name"],
                "shortDescription": {"text": meta["shortDescription"]},
                "helpUri": "https://github.com/example/pragyalint",
            }
            for rule, meta in _RULES.items()
        ],
    }
}


def format_sarif(report: AnalysisReport) -> str:
    results: List[Dict[str, Any]] = []
    for finding in report.findings:
        loc = None
        if finding.file and finding.line:
            region = {"startLine": finding.line}
            if finding.column:
                region["startColumn"] = finding.column + 1
            loc = {
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.file.replace("\\", "/")},
                    "region": region,
                }
            }
        results.append(
            {
                "ruleId": finding.rule,
                "level": _LEVEL.get(finding.confidence, "warning"),
                "message": {"text": finding.message},
                "locations": [loc] if loc else [],
            }
        )

    doc = {
        "$schema": (
            "https://json.schemastore.org/sarif-2.1.0.json"
        ),
        "version": "2.1.0",
        "runs": [
            {
                "tool": _TOOL,
                "results": results,
            }
        ],
    }
    return json.dumps(doc, indent=2)


__all__ = ["format_sarif"]
