"""Shared pytest helpers: build tiny sample projects in temp dirs."""

from __future__ import annotations

import os

from pragyalint.analyzer import analyze


def write_project(files: dict) -> str:
    """Create a temp dir containing the given relative-path->content map."""
    import tempfile

    d = tempfile.mkdtemp(prefix="pragyalint-test-")
    for rel, content in files.items():
        path = os.path.join(d, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    return d


def run(files: dict, **kwargs):
    """Write a project and analyze it, returning the report."""
    if "dir" in kwargs:
        d = kwargs.pop("dir")
    else:
        d = None
    import tempfile

    d = tempfile.mkdtemp(prefix="pragyalint-test-") if d is None else d
    for rel, content in files.items():
        path = os.path.join(d, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    return analyze(d, **kwargs)


def findings_by_rule(report, rule):
    return [f for f in report.findings if f.rule == rule]
