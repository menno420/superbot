"""Tests for the fuzzy command resolver (``utils.command_resolution``).

Covers the two-gate auto-correct derivation (lexical isolation +
non-destructive) and the AUTO / SUGGEST / NONE classification, including
the ambiguity guard.  A drift guard builds the token map from the *live*
command surface and asserts every auto-derived entry is still isolated.
"""

from __future__ import annotations

import pytest

from utils import command_resolution as cr
from utils.synonyms import COMMAND_SYNONYMS

# A small synthetic surface that mirrors the real one's shape: a couple of
# isolated read-only commands, a destructive one, and two mutually-close
# commands that must stay suggestion-only.
_TOKEN_MAP = {
    "serverstats": "serverstats",
    "leaderboard": "leaderboard",
    "top": "leaderboard",
    "ban": "ban",
    "bann": "ban",  # alias close to "ban"
    "warn": "warn",
    "warns": "warn",
    "rank": "rank",
    "lvl": "rank",
}


@pytest.fixture
def auto_set() -> frozenset[str]:
    return cr.derive_auto_correct_set(_TOKEN_MAP)


def test_derive_excludes_destructive(auto_set: frozenset[str]) -> None:
    assert "ban" not in auto_set
    assert "warn" not in auto_set


def test_derive_excludes_short_names() -> None:
    token_map = {"bj": "bj", "blackjack": "blackjack"}
    derived = cr.derive_auto_correct_set(token_map)
    assert "bj" not in derived  # below min length
    assert "blackjack" in derived


def test_derive_includes_isolated_readonly(auto_set: frozenset[str]) -> None:
    assert "serverstats" in auto_set
    assert "leaderboard" in auto_set
    assert "rank" in auto_set


def test_isolated_typo_auto_runs(auto_set: frozenset[str]) -> None:
    res = cr.classify("serverstas", _TOKEN_MAP, auto_set)
    assert res.outcome is cr.Outcome.AUTO
    assert res.command == "serverstats"


def test_destructive_typo_suggests_never_auto(auto_set: frozenset[str]) -> None:
    # "bann" is an exact alias of the destructive "ban" -> suggest, never auto.
    res = cr.classify("bann", _TOKEN_MAP, auto_set)
    assert res.outcome is cr.Outcome.SUGGEST
    assert res.command == "ban"


def test_exact_synonym_of_safe_command_auto_runs(auto_set: frozenset[str]) -> None:
    # "lvl" is an exact synonym for the safe, isolated "rank".
    res = cr.classify("lvl", _TOKEN_MAP, auto_set)
    assert res.outcome is cr.Outcome.AUTO
    assert res.command == "rank"


def test_ambiguous_match_suggests() -> None:
    # Two equally-close commands -> ambiguous -> suggest the best, never auto.
    token_map = {"settings": "settings", "setting": "setting"}
    auto_set = cr.derive_auto_correct_set(token_map)
    res = cr.classify("settngs", token_map, auto_set)
    assert res.outcome is cr.Outcome.SUGGEST


def test_no_close_match_returns_none(auto_set: frozenset[str]) -> None:
    res = cr.classify("zzzzzzplugh", _TOKEN_MAP, auto_set)
    assert res.outcome is cr.Outcome.NONE
    assert res.command is None


def test_empty_token_returns_none(auto_set: frozenset[str]) -> None:
    assert cr.classify("", _TOKEN_MAP, auto_set).outcome is cr.Outcome.NONE


def test_auto_set_entries_are_isolated() -> None:
    """Drift guard against the synonym table.

    Every auto-derived entry must remain lexically isolated: rebuilding the
    derivation must be idempotent, and no entry may be a close match to a
    token owned by a different command.  If a future command/synonym collides
    with an allowlisted name, this fails — forcing a conscious review.
    """
    import difflib

    token_map: dict[str, str] = {}
    for canonical, synonyms in COMMAND_SYNONYMS.items():
        token_map.setdefault(canonical, canonical)
        for syn in synonyms:
            token_map.setdefault(syn.lower(), canonical)

    auto_set = cr.derive_auto_correct_set(token_map)
    for name in auto_set:
        others = [tok for tok, owner in token_map.items() if owner != name]
        assert not difflib.get_close_matches(
            name, others, n=1, cutoff=0.8
        ), f"{name!r} is in the auto-correct set but collides with another token"
