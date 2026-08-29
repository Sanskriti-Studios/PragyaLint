"""Tests for the opt-in fix engine."""

from __future__ import annotations

import os

from pragyalint.analyzer import analyze
from pragyalint.fixer import apply_fixes
from tests.helpers import run as analyze_dir


def _analyze(dirpath, **kw):
    return analyze(dirpath, **kw)


def _read(path):
    with open(path) as fh:
        return fh.read()


def test_dry_run_deletes_nothing(tmp_path):
    (tmp_path / "main.py").write_text("x = 1\n")
    (tmp_path / "orphan.py").write_text("y = 2\n")
    report = _analyze(str(tmp_path))
    result = apply_fixes(report, targets=["files"], dry_run=True)
    assert result.applied == []
    assert result.dry_run == ["delete " + str(tmp_path / "orphan.py")]
    assert (tmp_path / "orphan.py").exists()


def test_delete_unreachable_file(tmp_path):
    (tmp_path / "main.py").write_text("x = 1\n")
    (tmp_path / "orphan.py").write_text("y = 2\n")
    report = _analyze(str(tmp_path))
    result = apply_fixes(report, targets=["files"], dry_run=False)
    assert result.applied == ["delete " + str(tmp_path / "orphan.py")]
    assert not (tmp_path / "orphan.py").exists()
    assert (tmp_path / "main.py").exists()


def test_entry_and_package_not_deleted(tmp_path):
    (tmp_path / "main.py").write_text("from pkg import mod\nmod.x\n")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "mod.py").write_text("x = 1\n")
    report = _analyze(str(tmp_path))
    result = apply_fixes(report, targets=["files"], dry_run=False)
    for action in result.applied:
        assert "main.py" not in action
        assert "__init__.py" not in action


def test_remove_unused_import_whole_line(tmp_path):
    (tmp_path / "main.py").write_text("import os\nimport sys\nprint(sys.path)\n")
    report = _analyze(str(tmp_path))
    result = apply_fixes(report, targets=["imports"], dry_run=False)
    assert result.applied == ["remove unused imports in " + str(tmp_path / "main.py")]
    assert "import os" not in _read(str(tmp_path / "main.py"))
    assert "import sys" in _read(str(tmp_path / "main.py"))


def test_remove_unused_name_from_multi_import(tmp_path):
    (tmp_path / "main.py").write_text(
        "from math import sqrt, cos\nprint(sqrt(4))\n"
    )
    report = _analyze(str(tmp_path))
    apply_fixes(report, targets=["imports"], dry_run=False)
    content = _read(str(tmp_path / "main.py"))
    assert "cos" not in content
    assert "sqrt" in content


def test_confidence_gates_exports_fix(tmp_path):
    # dead2 is a MEDIUM unused export; default confidence=high should skip it.
    (tmp_path / "main.py").write_text("import helper\nhelper.keep()\n")
    (tmp_path / "helper.py").write_text(
        "def keep():\n    return 1\n\ndef dead():\n    return 2\n"
    )
    report = _analyze(str(tmp_path))
    result = apply_fixes(report, targets=["exports"], min_confidence="high")
    assert result.applied == []
    # with medium confidence it IS removed
    report2 = _analyze(str(tmp_path))
    result2 = apply_fixes(report2, targets=["exports"], min_confidence="medium")
    assert result2.applied
    assert "def dead" not in _read(str(tmp_path / "helper.py"))
    assert "def keep" in _read(str(tmp_path / "helper.py"))


def test_all_reexport_protected_without_force(tmp_path):
    (tmp_path / "__init__.py").write_text(
        "from .mod import api\n__all__ = ['api']\n"
    )
    (tmp_path / "mod.py").write_text("def api():\n    pass\n")
    report = _analyze(str(tmp_path))
    result = apply_fixes(report, targets=["exports"], min_confidence="medium")
    # `api` is listed in __all__, so its definition must not be removed w/o --force
    assert result.applied == []


def test_fix_result_to_dict():
    from pragyalint.fixer import FixResult

    r = FixResult()
    r.record("delete x.py", dry_run=True)
    r.record("delete y.py", dry_run=False)
    d = r.to_dict()
    assert d["dry_run"] == ["delete x.py"]
    assert d["applied"] == ["delete y.py"]
