"""Tests for ``scripts/completion_scoreboard.py`` — the feature-completion scoreboard.

Exercises the pure tally core on synthetic ledger text (including the glyph-isolation
guarantee that keeps the doc's explanatory tables out of the count and skips the
generated block), and asserts the committed ledger README block is in sync.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "completion_scoreboard.py"


@pytest.fixture(scope="module")
def cs():
    spec = importlib.util.spec_from_file_location("completion_scoreboard_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tally_counts_bare_state_words(cs):
    text = "\n".join(
        [
            "| Unit | State |",
            "|---|---|",
            "| A | unassessed |",
            "| B | assessed |",
            "| C | certified |",
            "| D | unassessed |",
        ],
    )
    t = cs.tally(text)
    assert (t.unassessed, t.assessed, t.certified, t.total) == (2, 1, 1, 4)


def test_glyph_prefixed_cells_are_not_counted(cs):
    """The doc's ``▢ unassessed`` legend/example cells must not inflate the count."""
    text = "\n".join(
        [
            "| State | Meaning |",
            "|---|---|",
            "| ▢ unassessed | no cert |",
            "| ◐ assessed | scored |",
            "| ✔ certified | signed |",
            "| real | assessed |",
        ],
    )
    t = cs.tally(text)
    # Only the bare "assessed" row counts; the three glyph rows are ignored.
    assert (t.unassessed, t.assessed, t.certified, t.total) == (0, 1, 0, 1)


def test_generated_block_is_skipped(cs):
    text = "\n".join(
        [
            cs.START,
            "| ✔ certified | 9 | 100% |",
            "| something | certified |",
            cs.END,
            "| Unit | State |",
            "|---|---|",
            "| A | certified |",
        ],
    )
    # The block between markers (which contains a bare 'certified' cell) is stripped,
    # so only the single ledger row counts.
    t = cs.tally(text)
    assert (t.certified, t.total) == (1, 1)


def test_pct_safe_on_empty(cs):
    t = cs.Tally()
    assert t.total == 0
    assert t.pct(0) == 0


def test_committed_ledger_scoreboard_is_in_sync(cs):
    """The checked-in scoreboard block must match a fresh render (run --write if not)."""
    current = cs.LEDGER.read_text(encoding="utf-8")
    rendered = cs.render(cs.tally(current))
    assert cs._inject(rendered) == current, (
        "completion ledger scoreboard is stale — run "
        "`python3.10 scripts/completion_scoreboard.py --write`"
    )
