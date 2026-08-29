"""Tests for the module graph builder."""

from __future__ import annotations

from pragyalint.graph import ModuleGraphBuilder
from tests.helpers import run


def test_conventional_entry_recognition():
    report = run({"main.py": "x = 1"})
    assert report.entry_points == ["main"]


def test_app_and_cli_recognized_as_entries():
    for name in ("app.py", "cli.py", "setup.py", "__main__.py"):
        report = run({name: ""})
        assert report.entry_points, f"{name} should be an entry"


def test_unreachable_file_flagged():
    report = run(
        {
            "main.py": "import helper\n",
            "helper.py": "x = 1\n",
            "orphan.py": "y = 2\n",
        }
    )
    assert [f.extra["module"] for f in report.findings if f.rule == "unused_file"] == [
        "orphan"
    ]


def test_package_init_container_not_flagged():
    report = run(
        {
            "main.py": "from pkg.mod import x\nx\n",
            "pkg/__init__.py": "",
            "pkg/mod.py": "x = 1\n",
        }
    )
    unreachable = [f.extra["module"] for f in report.findings if f.rule == "unused_file"]
    assert unreachable == []


def test_relative_import_resolution():
    report = run(
        {
            "main.py": "from pkg import helper\nhelper.x\n",
            "pkg/__init__.py": "",
            "pkg/helper.py": "x = 1\n",
        }
    )
    assert report.summary.reachable_files == 3
    assert [f.extra["module"] for f in report.findings if f.rule == "unused_file"] == []


def test_dynamic_import_keeps_reachable():
    report = run(
        {
            "main.py": 'import importlib\nimportlib.import_module("plug")\n',
            "plug.py": "value = 42\n",
        }
    )
    unreachable = [f.extra["module"] for f in report.findings if f.rule == "unused_file"]
    assert unreachable == []


def test_cycle_detection():
    report = run(
        {
            "main.py": "import a\na.x\n",
            "a.py": "import b\nb.y\n",
            "b.py": "import a\na.z\n",
        },
        detect_cycles=True,
    )
    assert report.cycles
