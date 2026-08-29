"""Tests for the unused export and local-definition finders."""

from __future__ import annotations

from tests.helpers import findings_by_rule, run


def test_unused_export_flagged():
    report = run(
        {
            "main.py": "import helper\nhelper.used()\n",
            "helper.py": "def used():\n    return 1\n\ndef unused():\n    return 2\n",
        }
    )
    names = [f.extra["name"] for f in findings_by_rule(report, "unused_export")]
    assert "unused" in names
    assert "used" not in names


def test_entry_exports_not_flagged_by_default():
    report = run({"main.py": "def entry_fn():\n    pass\n"})
    names = [f.extra["name"] for f in findings_by_rule(report, "unused_export")]
    assert "entry_fn" not in names


def test_entry_exports_flagged_with_option():
    report = run(
        {"main.py": "def entry_fn():\n    pass\n"},
        include_entry_exports=True,
    )
    names = [f.extra["name"] for f in findings_by_rule(report, "unused_export")]
    assert "entry_fn" in names


def test_unused_function_flagged():
    report = run(
        {
            "main.py": "import helper\nhelper.used()\n",
            "helper.py": "def used():\n    return 1\n\ndef unused():\n    return 2\n",
        }
    )
    names = [
        f.extra["name"] for f in findings_by_rule(report, "unused_local")
    ]
    assert "unused" in names
    assert "used" not in names


def test_main_called_under_dunder_not_flagged():
    report = run(
        {
            "main.py": (
                "def main():\n"
                "    print('hi')\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            )
        }
    )
    names = [
        f.extra["name"] for f in findings_by_rule(report, "unused_local")
    ]
    assert "main" not in names
