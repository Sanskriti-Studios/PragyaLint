"""Human-readable terminal report formatting with simple ANSI colors."""

from __future__ import annotations

from typing import List

from pragyalint.models import AnalysisReport, Confidence

_RESET = "\x1b[0m"

_COLORS = {
    Confidence.HIGH: "\x1b[31m",   # red
    Confidence.MEDIUM: "\x1b[33m",  # yellow
    Confidence.LOW: "\x1b[36m",     # cyan
}

_ICONS = {
    Confidence.HIGH: "\u2716",  # ✖
    Confidence.MEDIUM: "\u26a0",  # ⚠
    Confidence.LOW: "\u2139",     # ℹ
}


def format_terminal(report: AnalysisReport, color: bool = True) -> str:
    lines: List[str] = []
    by_file: dict = {}
    for finding in report.findings:
        by_file.setdefault(finding.file or "(project)", []).append(finding)

    if not report.findings:
        lines.append(f"{_green('No dead code found.')} clean \u2728")

    for file, findings in by_file.items():
        lines.append(file)
        for finding in findings:
            loc = ""
            if finding.line is not None:
                loc = f":{finding.line}"
                if finding.column is not None:
                    loc += f":{finding.column}"
            marker = f"{_ICONS.get(finding.confidence, '')} "
            conf = finding.confidence.upper()
            if color:
                marker = f"{_COLORS.get(finding.confidence, '')}{marker}{_RESET}"
                conf = f"{_COLORS.get(finding.confidence, '')}{conf}{_RESET}"
            lines.append(f"  {loc:<8} {marker} [{conf:<6}] {finding.message}")
        lines.append("")

    s = report.summary
    summary = (
        f"\n{_bold(str(s.findings))} findings in {_bold(str(s.total_files))} files "
        f"({_bold(str(s.reachable_files))} reachable)."
    )
    lines.append(summary)
    parts = []
    for conf in Confidence.ORDER:
        count = s.by_confidence.get(conf, 0)
        if count:
            parts.append(f"{_COLORS.get(conf, '')}{count} {conf}{_RESET}")
    if parts:
        lines.append("  " + " | ".join(parts))
    return "\n".join(lines)


def _green(text: str) -> str:
    return f"\x1b[32m{text}\x1b[0m"


def _bold(text: str) -> str:
    return f"\x1b[1m{text}\x1b[0m"


__all__ = ["format_terminal"]
