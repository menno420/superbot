"""CI-parity guard for scripts/check_quality.py — the "true CI mirror".

`check_quality.py` is only trustworthy if its formatter scope matches
`.github/workflows/code-quality.yml` exactly (*"green here means green in CI"*).
They drifted once: CI switched isort from a broken `--skip-glob <regex>` to
directory-name `--skip` flags (2026-06-15), but the script kept the old glob, so
the mirror silently scanned `tests/` and threw false-red isort failures CI never
would. This test pins the black/isort/ruff *exclude scopes* of the two in sync so
that class can't recur.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "scripts" / "check_quality.py"
_WORKFLOW = _REPO / ".github" / "workflows" / "code-quality.yml"

#: The directories CI excludes from every formatter (the single canonical set).
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


def _dirs_from_regex_alternation(pattern: str) -> set[str]:
    """``(\\.github|tests|venv)`` → ``{".github", "tests", "venv"}``."""
    inner = pattern.strip().lstrip("(").rstrip(")")
    return {part.replace("\\.", ".") for part in inner.split("|")}


# --- the script's own declared scope --------------------------------------


def test_check_quality_declares_the_canonical_scope(mod):
    assert _dirs_from_regex_alternation(mod._BLACK_EXCLUDE) == _EXPECTED_DIRS
    assert set(mod._ISORT_SKIP_DIRS) == _EXPECTED_DIRS
    assert set(mod._RUFF_EXCLUDE.split(",")) == _EXPECTED_DIRS


# --- the workflow's actual scope (parsed from the YAML run: lines) ---------


def test_workflow_black_scope_matches(workflow_text):
    m = re.search(r"black --check \. --exclude '([^']*)'", workflow_text)
    assert m, "could not find the black --exclude line in code-quality.yml"
    assert _dirs_from_regex_alternation(m.group(1)) == _EXPECTED_DIRS


def test_workflow_isort_scope_matches(workflow_text):
    # isort uses repeated `--skip <dir>` (NOT --skip-glob — that was the bug).
    m = re.search(r"isort --check-only \. (.+)", workflow_text)
    assert m, "could not find the isort line in code-quality.yml"
    skips = set(re.findall(r"--skip (\S+)", m.group(1)))
    assert skips == _EXPECTED_DIRS
    assert "--skip-glob" not in m.group(1)  # the regex-in-a-glob trap stays gone


def test_workflow_ruff_scope_matches(workflow_text):
    m = re.search(r"ruff check \. --exclude (\S+)", workflow_text)
    assert m, "could not find the ruff --exclude line in code-quality.yml"
    assert set(m.group(1).split(",")) == _EXPECTED_DIRS


def test_mirror_and_workflow_agree_per_tool(mod, workflow_text):
    """The whole point: the script's scope == the workflow's scope, per tool."""
    black = re.search(r"black --check \. --exclude '([^']*)'", workflow_text)
    isort = re.search(r"isort --check-only \. (.+)", workflow_text)
    ruff = re.search(r"ruff check \. --exclude (\S+)", workflow_text)
    assert _dirs_from_regex_alternation(mod._BLACK_EXCLUDE) == (
        _dirs_from_regex_alternation(black.group(1))
    )
    assert set(mod._ISORT_SKIP_DIRS) == set(re.findall(r"--skip (\S+)", isort.group(1)))
    assert set(mod._RUFF_EXCLUDE.split(",")) == set(ruff.group(1).split(","))
