"""JSON report formatting."""

from __future__ import annotations

import json
from typing import Any

from pragyalint.models import AnalysisReport


def format_json(report: AnalysisReport, indent: int = 2) -> str:
    """Render the report as a JSON document."""
    return json.dumps(report.to_dict(), indent=indent, default=_json_default)


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return str(obj)


__all__ = ["format_json"]
