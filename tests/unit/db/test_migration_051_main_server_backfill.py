"""PR-7 — command-access main-server backfill migration.

The migration is data-only and idempotent.  Without a real Postgres
in unit CI we can still pin the SQL shape so a future drive-by edit
that, say, drops ``ON CONFLICT DO NOTHING`` or switches the lookup
table away from ``panel_anchors`` would fail this test.

Coverage:

* References the canonical pre-PR-7 main-server channel IDs.
* Targets both tables introduced in migration 050.
* Uses ``ON CONFLICT DO NOTHING`` on both INSERTs so re-run is safe.
* Discovers the guild_id by joining through ``panel_anchors`` (the
  broadest guild-scoped table — see the migration header for the
  rationale).
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MIGRATION = (
    _REPO_ROOT / "disbot" / "migrations" / "051_command_access_main_server_backfill.sql"
)


def _src() -> str:
    return _MIGRATION.read_text()


def test_migration_file_exists():
    assert _MIGRATION.is_file(), f"{_MIGRATION} missing"


def test_migration_references_canonical_channel_ids():
    """The two hardcoded IDs that were ``config.ALLOWED_CHANNELS``'
    fallback set pre-PR-7 must both appear so the main server's
    historical allowed-channels are preserved.
    """
    src = _src()
    assert "1348795460948590622" in src
    assert "1403818013408624642" in src


def test_migration_targets_both_command_access_tables():
    src = _src()
    assert "INSERT INTO guild_command_access_policy" in src
    assert "INSERT INTO guild_command_access_channels" in src


def test_migration_uses_panel_anchors_for_guild_id_lookup():
    """``panel_anchors`` is the broadest guild-scoped table — every
    guild that has restored a panel since on_ready has rows there.
    Switching to a less-populated table would make the backfill miss
    deployments the upgrade actually intends to cover.
    """
    src = _src()
    assert "FROM panel_anchors" in src
    # Both INSERTs filter on the same channel-id whitelist.
    assert src.count("WHERE channel_id IN") >= 2


def test_migration_is_idempotent_on_both_tables():
    """``ON CONFLICT DO NOTHING`` on both INSERTs lets the migration
    re-run cleanly if an operator has already configured the policy
    through the settings UI before the migration is applied (the
    apply-order is engine-controlled but the safety net stays).
    """
    src = _src()
    assert src.count("ON CONFLICT") >= 2
    assert "DO NOTHING" in src


def test_migration_attributes_backfill_to_system_via_null_actor():
    """Audit metadata: the backfill is system-driven, not
    operator-driven, so ``updated_by`` and ``created_by`` are
    deliberately NULL rather than seeded with an arbitrary id.

    Each NULL must be explicitly cast to ``bigint`` because Postgres
    otherwise infers a bare NULL literal in a SELECT projection as
    ``text``, which clashes with the BIGINT columns and aborts the
    INSERT at runtime. Pre-fix this took the bot down in production.
    """
    # Strip ``-- ...`` comments so the scan only sees executable SQL.
    sql_lines = [
        line.split("--", 1)[0]
        for line in _src().splitlines()
        if not line.startswith("--")
    ]
    executable_sql = "\n".join(sql_lines)

    # Both NULLs (updated_by + created_by) must be cast, not just one.
    assert (
        executable_sql.count("NULL::bigint") >= 2
    ), "Migration 051 must cast both NULL projections to bigint."
    # And no bare NULL literal survives in a projection — only the
    # cast form is acceptable.
    import re

    bare_nulls = re.findall(r"NULL(?!::)", executable_sql)
    assert not bare_nulls, (
        "Bare NULL literal in migration 051 — every NULL in a SELECT "
        "projection must be cast to bigint to match the BIGINT column."
    )
