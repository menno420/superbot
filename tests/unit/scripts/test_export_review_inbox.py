"""Tests for the owner-review-inbox parser in ``export_dashboard_data.py`` (B7).

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules, which are
not a package). The exporter is pure stdlib, so this runs in CI with no extra
dependencies. Mirrors ``test_export_dashboard_data.py``'s bug-book parser test —
the review parser is its Q-0169 cousin (``## REV-NNNN — area — STATUS``).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "export_dashboard_data.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("export_review_inbox_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_REVIEWS = """# Review inbox

## REV-0002 — economy-cog — OPEN

- **Review (owner):** the daily payout should scale with streak length.
- **Area:** economy cog

## REV-0001 — help command — RESOLVED (#1234)

- **Review (owner):** the help embed wraps badly on mobile.
- **Resolution:** rewrapped the embed in PR #1234.
"""


def test_parse_reviews_extracts_id_area_status_summary(mod):
    reviews = mod.parse_reviews(SAMPLE_REVIEWS)
    assert [r["id"] for r in reviews] == ["REV-0002", "REV-0001"]
    assert reviews[0]["status"] == "OPEN"
    assert reviews[0]["area"] == "economy-cog"
    assert "scale with streak length" in reviews[0]["summary"]


def test_parse_reviews_strips_pr_tag_from_resolved_status(mod):
    reviews = mod.parse_reviews(SAMPLE_REVIEWS)
    resolved = reviews[1]
    # The trailing "(#1234)" must not bleed into the status token.
    assert resolved["status"] == "RESOLVED"
    assert resolved["area"] == "help command"
    assert "wraps badly on mobile" in resolved["summary"]


def test_parse_reviews_handles_text_without_entries(mod):
    assert mod.parse_reviews("# Review inbox\n\nNo reviews yet.\n") == []


def test_parse_reviews_hyphenated_area_survives(mod):
    # Only the *last* dash delimits the status, so a hyphenated area is preserved.
    text = "## REV-0003 — blackjack-game-state — OPEN\n\n- **Review (owner):** x\n"
    reviews = mod.parse_reviews(text)
    assert len(reviews) == 1
    assert reviews[0]["area"] == "blackjack-game-state"
    assert reviews[0]["status"] == "OPEN"


def test_build_data_includes_reviews_section_and_counts(mod):
    data = mod.build_data()
    assert "reviews" in data
    reviews = data["reviews"]
    assert isinstance(reviews, list)
    assert data["meta"]["counts"]["reviews"] == len(reviews)
    assert data["meta"]["counts"]["reviews_open"] == sum(
        1 for r in reviews if r["status"].upper() == "OPEN"
    )
    for review in reviews:
        assert set(review) >= {"id", "area", "status", "summary"}
        assert review["id"].startswith("REV-")
