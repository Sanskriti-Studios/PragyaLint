"""Tests for config loading, output reporters, and should_fail."""

from __future__ import annotations

import json

from pragyalint.config import load_config
from pragyalint.models import Confidence, should_fail
from pragyalint.reporters import format_json, format_sarif, format_terminal
from tests.helpers import run


def test_toml_config_loaded(tmp_path):
    (tmp_path / "pragyalint.toml").write_text(
        'entry = ["src"]\nignore = ["gen/"]\nfail_on = "medium"\n'
    )
    cfg = load_config(str(tmp_path))
    assert cfg["entry"] == ["src"]
    assert cfg["ignore"] == ["gen/"]
    assert cfg["fail_on"] == "medium"


def test_pyproject_tool_section_loaded(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pragyalint]\nignore = ["migrations/"]\ndetect_cycles = true\n'
    )
    cfg = load_config(str(tmp_path))
    assert cfg["ignore"] == ["migrations/"]
    assert cfg["detect_cycles"] is True


def test_unknown_keys_ignored(tmp_path):
    (tmp_path / "pragyalint.toml").write_text('bogus_key = 1\nextensions = [".py"]\n')
    cfg = load_config(str(tmp_path))
    assert "bogus_key" not in cfg


def test_json_report_roundtrip():
    report = run({"main.py": "import os\n", "orphan.py": "x = 1\n"})
    doc = json.loads(format_json(report))
    assert doc["summary"]["findings"] > 0
    assert any(f["rule"] == "unused_import" for f in doc["findings"])


def test_sarif_report_shape():
    report = run({"main.py": "import os\n"})
    doc = json.loads(format_sarif(report))
    assert doc["version"] == "2.1.0"
    results = doc["runs"][0]["results"]
    assert any(r["ruleId"] == "unused_import" for r in results)


def test_terminal_report_nonempty():
    report = run({"main.py": "import os\n"})
    text = format_terminal(report, color=False)
    assert "findings" in text


def test_should_fail_high_threshold():
    report = run({"main.py": "import os\n"})  # produces a HIGH finding
    assert should_fail(report, Confidence.parse_min("high")) is True
    report2 = run(
        {
            "main.py": "import helper\nhelper.used()\n",
            "helper.py": "def used():\n    pass\n\ndef unused():\n    pass\n",
        }
    )
    # highest is a MEDIUM unused_export/unused_local finding
    assert should_fail(report2, Confidence.parse_min("high")) is False
    assert should_fail(report2, Confidence.parse_min("medium")) is True
