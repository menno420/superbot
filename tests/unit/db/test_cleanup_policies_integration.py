"""Real-Postgres integration for the cleanup-policy version marker (PR8).

Migration 058 adds ``cleanup_policies.policy_version`` (NOT NULL DEFAULT 1). This
suite drives it against a live database via ``utils.db.pool.init()`` (which
applies the full schema + every migration, including 058), then asserts the
observable behaviour: a legacy-shape insert that never mentions the column still
gets version 1 (DEFAULT backfill), and the read model surfaces it.

CI safety
---------
There is **no** shared Postgres fixture (``tests/conftest.py`` deliberately has
none) and CI (``code-quality.yml``) runs **no** Postgres service. The
module-local ``postgres_pool`` fixture below ``pytest.skip()``s cleanly when
``DATABASE_URL`` is unset (CI) or the database is unreachable (sandbox before
local Postgres is up), so this file is a no-op there and only runs where a real
database is available. Canonical sibling: ``test_health_findings_integration.py``.

Isolation
---------
Every row uses the ``_TEST_GUILD`` namespace; the fixture sweeps exactly that
guild's rows before and after each test. Tests run serially (CI and
``check_quality`` both invoke pytest without xdist), so this is safe.
"""

from __future__ import annotations

import os

import asyncpg
import pytest
import pytest_asyncio

from utils.db import governance as gov_db
from utils.db import pool

_TEST_GUILD = 800000000000000058


async def _sweep() -> None:
    await pool.execute(
        "DELETE FROM cleanup_policies WHERE guild_id = $1",
        (_TEST_GUILD,),
    )


@pytest_asyncio.fixture
async def postgres_pool():
    """Module-local live-Postgres pool; skips cleanly when none is available."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL unset — real-Postgres integration test skipped (CI)")
    try:
        await pool.init()
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(
            f"Postgres unreachable ({type(exc).__name__}) — integration test skipped",
        )
    await _sweep()
    try:
        yield pool
    finally:
        await _sweep()
        await pool.close()


async def test_legacy_insert_backfills_policy_version_to_one(postgres_pool):
    """A legacy-shape write (the 3 columns, no policy_version) still resolves to
    version 1 via the column DEFAULT — proving 058 applied and backfills.
    """
    await gov_db.set_cleanup_policy(_TEST_GUILD, "guild", _TEST_GUILD, True, True, 5)

    rows = await gov_db.get_all_cleanup_for_guild(_TEST_GUILD)
    assert len(rows) == 1
    row = rows[0]
    assert row["policy_version"] == 1
    assert row["scope_type"] == "guild"
    assert row["delete_invalid_commands"] is True
    assert row["delete_after_seconds"] == 5


async def test_get_all_cleanup_returns_policy_version_per_scope(postgres_pool):
    """The read model returns policy_version for every scope row."""
    await gov_db.set_cleanup_policy(_TEST_GUILD, "guild", _TEST_GUILD, True, True, 5)
    await gov_db.set_cleanup_policy(_TEST_GUILD, "channel", 111, True, False, 10)

    rows = await gov_db.get_all_cleanup_for_guild(_TEST_GUILD)
    assert {r["scope_type"] for r in rows} == {"guild", "channel"}
    assert all(r.get("policy_version") == 1 for r in rows)


async def test_guild_default_keyed_by_guild_id_resolves(postgres_pool):
    """Regression (PR9 root-cause fix): a guild-default policy keyed by guild_id
    is actually read by the resolver and yields a GUILD_OVERRIDE.
    """
    from governance.cleanup import resolve_cleanup_policy
    from governance.models import GovernanceContext, PolicySource
    from services.cleanup_levels import cleanup_scope_id

    sid = cleanup_scope_id("guild", _TEST_GUILD, None)
    assert sid == _TEST_GUILD
    await gov_db.set_cleanup_policy(_TEST_GUILD, "guild", sid, True, True, 2)

    # A channel with no own/category override inherits the guild default.
    ctx = GovernanceContext(guild_id=_TEST_GUILD, channel_id=999000111)
    policy = await resolve_cleanup_policy(ctx)
    assert policy.resolved_from == PolicySource.GUILD_OVERRIDE
    assert policy.delete_after_seconds == 2


async def test_legacy_guild_scope_zero_is_not_resolved(postgres_pool):
    """The pre-fix convention (scope_id=0) is a silent no-op: the resolver looks
    up guild policy at scope_id=guild_id, so a 0 row is never read.  Guards
    against a regression back to 0.
    """
    from governance.cleanup import resolve_cleanup_policy
    from governance.models import GovernanceContext, PolicySource

    await gov_db.set_cleanup_policy(_TEST_GUILD, "guild", 0, True, True, 2)
    ctx = GovernanceContext(guild_id=_TEST_GUILD, channel_id=999000111)
    policy = await resolve_cleanup_policy(ctx)
    assert policy.resolved_from == PolicySource.FALLBACK_DEFAULT
    assert policy.delete_after_seconds == 5


async def test_delete_cleanup_policy_removes_row_and_reports(postgres_pool):
    """delete_cleanup_policy clears the exact row (incl. a legacy scope_id=0 one)
    and reports whether a row was actually removed.
    """
    # A legacy guild row + a live channel row.
    await gov_db.set_cleanup_policy(_TEST_GUILD, "guild", 0, True, True, 2)
    await gov_db.set_cleanup_policy(_TEST_GUILD, "channel", 111, True, False, 10)
    assert len(await gov_db.get_all_cleanup_for_guild(_TEST_GUILD)) == 2

    # Removing the legacy row by its literal key returns True and leaves the
    # channel row intact.
    removed = await gov_db.delete_cleanup_policy(_TEST_GUILD, "guild", 0)
    assert removed is True
    remaining = await gov_db.get_all_cleanup_for_guild(_TEST_GUILD)
    assert [r["scope_type"] for r in remaining] == ["channel"]

    # Removing something that isn't there is a no-op → False.
    assert await gov_db.delete_cleanup_policy(_TEST_GUILD, "guild", 0) is False
