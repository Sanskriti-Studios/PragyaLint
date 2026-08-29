"""Tests for unused import detection."""

from __future__ import annotations

from tests.helpers import findings_by_rule, run


def test_unused_import_flagged():
    report = run(
        {
            "main.py": (
                "import os\n"
                "import sys\n"
                "print(os.path)\n"
            ),
        }
    )
    imports = [
        f.extra["import"] for f in findings_by_rule(report, "unused_import")
    ]
    assert "sys" in imports
    assert "os" not in imports


def test_unused_from_import_flagged():
    report = run({"main.py": "from math import sqrt, cos\nprint(sqrt(4))\n"})
    imports = [
        f.extra["import"] for f in findings_by_rule(report, "unused_import")
    ]
    assert "cos" in imports
    assert "sqrt" not in imports


def test_all_reexport_is_used():
    report = run(
        {
            "__init__.py": (
                "from .api import handler\n"
                "__all__ = ['handler']\n"
            ),
            "api.py": "def handler():\n    return 1\n",
        }
    )
    imports = [
        f.extra["import"] for f in findings_by_rule(report, "unused_import")
    ]
    assert "handler" not in imports


def test_future_import_never_flagged():
    report = run({"main.py": "from __future__ import annotations\ndef f() -> None:\n    pass\n"})
    imports = [
        f.extra["import"] for f in findings_by_rule(report, "unused_import")
    ]
    assert imports == []
