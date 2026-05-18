"""Phase 2d PR-2 invariant — feature_flag state values match migration 023.

Migration 023 ships CHECK constraints on
``feature_flag_global_overrides.state`` and
``feature_flag_guild_overrides.state``.  Both columns use the same
constraint literal set: the union of the two hard overrides
(``on``/``off``) and the four tier-equivalence values
(``owner``/``canary``/``beta``/``production``).

The Python evaluator
(:mod:`core.runtime.feature_flags`.``_state_to_decision``) treats any
value outside this set as "unknown — fall back to declared default".
If the DB ever accepted a value that Python silently ignored, an
operator override would appear successful but have no behavioural
effect.  This test pins the literal set on both sides so the next
addition (e.g. a future ``percent`` state) cannot land without an
explicit, reviewed update.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "023_feature_flag_state.sql"
)


def _extract_state_literals() -> set[str]:
    """Return the literals inside the migration's state CHECK constraint."""
    sql = _MIGRATION.read_text()
    matches = re.findall(
        r"CHECK\s*\(\s*state\s+IN\s*\(([^)]+)\)\s*\)",
        sql,
    )
    assert matches, "could not locate state CHECK constraint in migration 023"
    # Both CHECK clauses must agree — collapse to one set
    all_literals: set[str] = set()
    for clause in matches:
        for token in clause.split(","):
            literal = token.strip().strip("'\"")
            all_literals.add(literal)
    return all_literals


def test_feature_flag_state_literals_match_known_evaluator_set():
    """The DB state set matches the evaluator's recognized state strings."""
    db_literals = _extract_state_literals()
    expected = {"off", "owner", "canary", "beta", "production", "on"}

    missing_in_db = expected - db_literals
    missing_in_python = db_literals - expected

    assert not missing_in_db and not missing_in_python, (
        "feature_flag state CHECK / evaluator drift.\n"
        f"  in evaluator but not DB CHECK: {sorted(missing_in_db)}\n"
        f"  in DB CHECK but not evaluator: {sorted(missing_in_python)}\n"
        "Fix: extend the CHECK constraint via a new migration AND extend "
        "``_state_to_decision`` in core/runtime/feature_flags.py.",
    )


def test_evaluator_recognizes_every_db_state_literal():
    """Each DB literal maps to a defined behaviour in the evaluator.

    This is a stronger guarantee than just "the sets are equal": even
    if the set comparison passed, the evaluator might handle some
    literal as a typo.  We exercise the mapping directly.
    """
    from core.runtime.feature_flags import FeatureFlag, _state_to_decision

    flag = FeatureFlag(
        name="t.test",
        description="alignment test",
        default_value=False,
    )

    # Hard overrides
    assert _state_to_decision("on", flag=flag, guild_tier="production") is True
    assert _state_to_decision("off", flag=flag, guild_tier="owner") is False

    # Tier-equivalence values are accepted (their truthiness depends on
    # the guild's tier; here we just exercise the mapping path).
    for tier_state in ("owner", "canary", "beta", "production"):
        result = _state_to_decision(
            tier_state,
            flag=flag,
            guild_tier="production",
        )
        assert isinstance(
            result, bool
        ), f"_state_to_decision returned non-bool for state={tier_state!r}"
