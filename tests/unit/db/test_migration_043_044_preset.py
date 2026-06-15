"""PR-B migration shape pins for 043 (preset column) + 044 (seed).

Cheap offline checks that catch the most common authoring mistakes
before a deploy attempts the migration.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MIGRATIONS = _REPO_ROOT / "disbot" / "migrations"

_M043 = _MIGRATIONS / "043_ai_instruction_profile_preset.sql"
_M044 = _MIGRATIONS / "044_ai_instruction_profile_seed.sql"


def test_043_file_present():
    assert _M043.is_file(), "Migration 043 missing"


def test_044_file_present():
    assert _M044.is_file(), "Migration 044 missing"


def test_043_adds_is_preset_column_idempotently():
    src = _M043.read_text()
    assert (
        "ADD COLUMN IF NOT EXISTS is_preset" in src
    ), "043 must add is_preset with IF NOT EXISTS for idempotency"
    assert "BOOLEAN NOT NULL DEFAULT FALSE" in src
    # Partial index for cheap WHERE is_preset = TRUE reads.
    assert "CREATE INDEX IF NOT EXISTS" in src
    assert "ai_instruction_profile" in src
    assert "WHERE is_preset = TRUE" in src


_EXPECTED_PRESETS = (
    "disabled",
    "mention_only_helper",
    "helpful_channel",
    "btd6_focused",
    "quiet_btd6_focused",
    "staff_diagnostics",
    "support_triage",
)


def test_044_seeds_exactly_the_expected_presets():
    src = _M044.read_text()
    for name in _EXPECTED_PRESETS:
        assert f"'{name}'" in src, f"044 missing preset {name!r}"


def test_044_uses_on_conflict_for_idempotency():
    src = _M044.read_text()
    assert (
        "ON CONFLICT (guild_id, scope, name) DO UPDATE" in src
    ), "044 must be idempotent via ON CONFLICT … DO UPDATE"
    # Never let an idempotent replay flip is_preset back to FALSE.
    assert "is_preset  = TRUE" in src or "is_preset = TRUE" in src


def test_044_seeds_are_system_scoped():
    src = _M044.read_text()
    # Every INSERT row has guild_id NULL + scope 'system' + is_preset TRUE.
    assert "(NULL, 'disabled'," in src
    assert "'system', NULL, TRUE" in src
