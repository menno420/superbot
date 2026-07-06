"""CI-parity guard for scripts/check_quality.py — the "true CI mirror".

`check_quality.py` is only trustworthy if its formatter scope matches
`.github/workflows/code-quality.yml` exactly (*"green here means green in CI"*).
They drifted once (2026-06-15): the mirror kept a stale isort `--skip-glob <regex>`
after CI moved to directory-name skips, so it silently scanned `tests/` and threw
false-red failures CI never would. ruff replaced black + isort (A3, 2026-07-06) — the
gate is now `ruff format` + `ruff check` — so this test pins the *exclude scope* of
those two invocations in sync between the script and the workflow.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "scripts" / "check_quality.py"
_WORKFLOW = _REPO / ".github" / "workflows" / "code-quality.yml"

#: The directories CI excludes from ruff (the single canonical set).
_EXPECTED_DIRS = {".github", "tests", "venv", "env", "build", "dist"}


def _load_check_quality():
    spec = importlib.util.spec_from_file_location("check_quality_ut", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_check_quality()


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return _WORKFLOW.read_text(encoding="utf-8")


# --- the script's own declared scope --------------------------------------


def test_check_quality_declares_the_canonical_scope(mod):
    assert set(mod._RUFF_EXCLUDE.split(",")) == _EXPECTED_DIRS


# --- the workflow's actual scope (parsed from the YAML run: lines) ---------


def test_workflow_ruff_format_scope_matches(workflow_text):
    m = re.search(r"ruff format --check \. --exclude (\S+)", workflow_text)
    assert m, "could not find the ruff format --exclude line in code-quality.yml"
    assert set(m.group(1).split(",")) == _EXPECTED_DIRS


def test_workflow_ruff_scope_matches(workflow_text):
    m = re.search(r"ruff check \. --exclude (\S+)", workflow_text)
    assert m, "could not find the ruff check --exclude line in code-quality.yml"
    assert set(m.group(1).split(",")) == _EXPECTED_DIRS


def test_no_black_or_isort_left_in_the_gate(workflow_text):
    # ruff replaced them (A3); a re-introduced black/isort step would silently
    # diverge from the mirror, which no longer runs them.
    assert "black --check" not in workflow_text
    assert "isort --check-only" not in workflow_text


def test_mirror_and_workflow_agree(mod, workflow_text):
    """The whole point: the script's ruff scope == the workflow's, for both invocations."""
    fmt = re.search(r"ruff format --check \. --exclude (\S+)", workflow_text)
    chk = re.search(r"ruff check \. --exclude (\S+)", workflow_text)
    assert set(mod._RUFF_EXCLUDE.split(",")) == set(fmt.group(1).split(","))
    assert set(mod._RUFF_EXCLUDE.split(",")) == set(chk.group(1).split(","))
