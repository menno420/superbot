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
    version 1 via the column DEFAULT — proving 058 applied and backfills."""
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
