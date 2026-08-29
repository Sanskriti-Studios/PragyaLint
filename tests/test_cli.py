"""End-to-end tests for the CLI via the run() function."""

from __future__ import annotations

import json

from pragyalint.cli import build_parser, run
from tests.helpers import run as analyze_dir


def test_help_mentions_analyze():
    import pytest

    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0


def test_cli_terminal_default():
    import tempfile, os

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "main.py"), "w") as fh:
        fh.write("import sys\n")
    code = run(["-r", d])
    assert code == 0


def test_cli_json_output():
    import tempfile, os

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "main.py"), "w") as fh:
        fh.write("import sys\n")
    import io, contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = run(["-r", d, "--json"])
    assert code == 0
    doc = json.loads(buf.getvalue())
    assert doc["summary"]["findings"] >= 1


def test_cli_fail_on_high():
    import tempfile, os

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "main.py"), "w") as fh:
        fh.write("import sys\n")  # produces a HIGH unused_import finding
    code = run(["-r", d, "--fail-on", "high"])
    assert code == 1


def test_cli_clean_project_no_fail():
    import tempfile, os

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "main.py"), "w") as fh:
        fh.write("def main():\n    print('hi')\nif __name__ == '__main__':\n    main()\n")
    code = run(["-r", d, "--fail-on", "high"])
    assert code == 0
