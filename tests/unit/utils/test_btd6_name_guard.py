"""Pure unit tests for the BTD6 name/number matching primitives."""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.btd6 import name_guard  # noqa: E402
from utils.btd6.keywords import has_btd6_context  # noqa: E402


def _matchers() -> name_guard.NameMatchers:
    return name_guard.build_matchers(
        canonicals={"Apex Plasma Master", "Dart Monkey", "Quincy", "Psi", "Adora"},
        aliases={"q", "ado", "brickell", "ice"},
    )


def test_short_canonical_names_kept():
    m = _matchers()
    # Distinctive short hero canonicals survive (>= 3 chars).
    assert "psi" in m.single
    assert "adora" in m.single
    assert "quincy" in m.single


def test_generic_and_short_aliases_dropped():
    m = _matchers()
    # Ultra-short aliases (q, ado) and common-word aliases (ice) are not
    # proper-name evidence.
    assert "q" not in m.single
    assert "ado" not in m.single
    assert "ice" not in m.single
    # A distinctive long alias survives.
    assert "brickell" in m.single


def test_multiword_names_are_substring_matchers():
    m = _matchers()
    assert "apex plasma master" in m.multi
    assert "dart monkey" in m.multi
    assert name_guard.multiword_names_present(
        "the Apex Plasma Master is strong", m
    ) == {"apex plasma master"}


def test_names_present_whole_word_vs_substring():
    m = _matchers()
    # Whole-word for single tokens: "quincy" matches, "quincyish" does not.
    assert "quincy" in name_guard.names_present("I picked Quincy today", m)
    assert "quincy" not in name_guard.names_present("quincyish nonsense", m)
    # Substring for multi-word phrases.
    assert "dart monkey" in name_guard.names_present("a dart monkey wall", m)


def test_normalize_numbers_strips_thousands_separators():
    assert name_guard.normalize_numbers("48,210") == name_guard.normalize_numbers(
        "48210"
    )
    assert name_guard.normalize_numbers("cost 1,000.50") == {"1000.50"}


def test_offending_numbers_comma_normalized_substring():
    # Grounded comma-formatted value covers a comma-free answer.
    assert name_guard.offending_numbers("it is 48210", "total 48,210 rbe") == ()
    # A genuinely absent value is flagged.
    assert "999999" in name_guard.offending_numbers("it is 999999", "total 48,210")
    # Substring leniency (mirrors claims_are_grounded): a short integer inside a
    # larger grounded number is not flagged.
    assert name_guard.offending_numbers("tier 5", "cost 150000") == ()


def test_has_btd6_context_discriminates_ordinary_chat():
    assert has_btd6_context("which heroes are in the game?") is True
    assert has_btd6_context("what's the strongest tower?") is True
    assert has_btd6_context("Who was Benjamin Franklin?") is False
    assert has_btd6_context("tell me about the weather") is False
