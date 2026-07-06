"""Tests for scripts/check_tool_pins.py — the three-places tool-pin guard.

The checker became a CI gate (`.github/workflows/tool-pins.yml`) after a lone
Dependabot bump of ruff in `requirements-dev.txt` (#1315) drifted from the
workflow + pre-commit pins and reached `main` (fixed #1317) — so it is now
load-bearing and gets its own tests (the Q-0105 "verify before you trust"
posture for a guard that can block merges).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "scripts" / "check_tool_pins.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_tool_pins_ut", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load()


# --- the parsers (pure on text) -------------------------------------------


def test_pins_parses_equals_pins(mod):
    # black/isort removed (A3) — only ruff + mypy are tracked now.
    text = "pip install ruff==0.15.14 mypy==2.1.0"
    got = {k: sorted(v) for k, v in mod._pins(text).items()}
    assert got == {
        "ruff": ["0.15.14"],
        "mypy": ["2.1.0"],
    }


def test_precommit_pins_maps_repo_to_tool_and_strips_v_prefix(mod):
    # The single ruff-pre-commit repo hosts both the ruff-format and ruff hooks
    # under one rev — one pin covers both (A3).
    text = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.14
    hooks:
      - id: ruff-format
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.1.0
    hooks: [{id: mypy}]
"""
    got = {k: sorted(v) for k, v in mod._precommit_pins(text).items()}
    # v-prefix stripped so v0.15.14 compares equal to the requirements 0.15.14.
    assert got == {
        "ruff": ["0.15.14"],
        "mypy": ["2.1.0"],
    }


# --- check() across three synthetic sources -------------------------------

_CI = "pip install ruff==0.15.14 mypy==2.1.0"
_DEV = "ruff==0.15.14\nmypy==2.1.0\n"
_PRECOMMIT = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.14
    hooks:
      - id: ruff-format
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.1.0
    hooks: [{id: mypy}]
"""


def _sources(tmp_path: Path, ci: str, dev: str, precommit: str):
    (tmp_path / "code-quality.yml").write_text(ci, encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text(dev, encoding="utf-8")
    (tmp_path / ".pre-commit-config.yaml").write_text(precommit, encoding="utf-8")
    return (
        ("code-quality.yml", tmp_path / "code-quality.yml"),
        ("requirements-dev.txt", tmp_path / "requirements-dev.txt"),
        (".pre-commit-config.yaml", tmp_path / ".pre-commit-config.yaml"),
    )


def test_check_passes_when_all_three_aligned(mod, tmp_path):
    assert mod.check(_sources(tmp_path, _CI, _DEV, _PRECOMMIT)) == []


def test_check_flags_dev_vs_ci_drift(mod, tmp_path):
    # The exact #1315 trap: requirements-dev.txt bumped alone.
    drifted = _DEV.replace("ruff==0.15.14", "ruff==0.15.18")
    problems = mod.check(_sources(tmp_path, _CI, drifted, _PRECOMMIT))
    assert any("ruff" in p and "disagree" in p for p in problems)


def test_check_flags_precommit_drift(mod, tmp_path):
    # The latent gap the old (two-file) checker missed: pre-commit alone drifts.
    drifted = _PRECOMMIT.replace("rev: v0.15.14", "rev: v0.15.18")
    problems = mod.check(_sources(tmp_path, _CI, _DEV, drifted))
    assert any("ruff" in p for p in problems)


def test_check_flags_pin_missing_in_one_place(mod, tmp_path):
    dev_without_mypy = _DEV.replace("mypy==2.1.0\n", "")
    problems = mod.check(_sources(tmp_path, _CI, dev_without_mypy, _PRECOMMIT))
    assert any("mypy" in p for p in problems)


def test_check_reports_missing_source_file(mod, tmp_path):
    sources = _sources(tmp_path, _CI, _DEV, _PRECOMMIT)
    (tmp_path / "requirements-dev.txt").unlink()
    problems = mod.check(sources)
    assert any("missing pin source" in p for p in problems)


# --- the real repo stays aligned (a live guard, not just a unit) -----------


def test_real_repo_pins_are_aligned(mod):
    assert (
        mod.check() == []
    ), "the repo's three pin sources have drifted — run the guard"
