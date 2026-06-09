"""Real-Postgres integration for the AI tool-orchestration profile (Phase 3).

Why this file exists
--------------------
``test_ai_orchestration_policy.py`` / ``test_ai_orchestration_mutation.py`` mock
the ``utils.db.ai`` reads/writes, so they pin the resolver + mutation contracts
but never run the actual migration-062 SQL: the new ``orchestration_profile``
columns, the column-only setters' ``ON CONFLICT`` (incl. the ``mode='inherit'``
insert for an orchestration-only channel/category write), and the generation
bump. This suite drives that SQL against a live database via ``pool.init()``
(which applies the full schema + every migration), then asserts the observable
precedence + projection behaviour end-to-end through the audited service seam.

CI safety
---------
There is **no** shared Postgres fixture and CI runs **no** Postgres service, so
the module-local ``postgres_pool`` fixture ``pytest.skip()``s cleanly when
``DATABASE_URL`` is unset (CI) or the DB is unreachable (sandbox before local
Postgres is up). It is a no-op there and only runs where a real DB is available.

Isolation
---------
Every row this suite writes uses a guild id in the reserved ``_GUILD_BASE``
range; the fixture sweeps exactly those rows from the three policy tables before
and after each test, so it never disturbs a booted bot's data. Tests run
serially, so the shared range is safe.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import asyncpg
import pytest
import pytest_asyncio

from services import ai_config_projection_service as projection
from services import ai_orchestration_mutation as mutation
from services import ai_orchestration_policy as orch
from services import ai_orchestration_presets as presets
from utils.db import pool

# Reserved guild-id range for this suite (swept on entry + exit).
_GUILD_BASE = 920_000_000_000_000_000
_GUILD_IDS = tuple(_GUILD_BASE + i for i in range(8))

_ADMIN = SimpleNamespace(
    id=4242,
    guild_permissions=SimpleNamespace(administrator=True),
)


async def _sweep() -> None:
    for table in ("ai_channel_policy", "ai_category_policy", "ai_guild_policy"):
        await pool.execute(
            f"DELETE FROM {table} WHERE guild_id = ANY($1::bigint[])",
            (list(_GUILD_IDS),),
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
    orch._reset_for_tests()
    await _sweep()
    try:
        yield pool
    finally:
        await _sweep()
        orch._reset_for_tests()
        await pool.close()


def _ctx(guild_id: int, channel_id: int = 1, category_id: int | None = None):
    return orch.OrchestrationContext(
        guild_id=guild_id,
        channel_id=channel_id,
        category_id=category_id,
    )


async def test_migration_062_columns_exist(postgres_pool) -> None:
    row = await pool.fetchone(
        """
        SELECT count(*) AS n FROM information_schema.columns
        WHERE column_name = 'orchestration_profile'
          AND table_name IN ('ai_guild_policy', 'ai_channel_policy',
                             'ai_category_policy')
        """,
        (),
    )
    assert row is not None and int(row["n"]) == 3


async def test_precedence_round_trip(postgres_pool) -> None:
    gid = _GUILD_IDS[0]
    chan, cat = 111, 222

    # Nothing set → compatible default.
    d = await orch.resolve(_ctx(gid, chan, cat))
    assert d.profile_key == presets.DEFAULT_PROFILE_KEY
    assert d.source == "default"

    # Guild → guild.
    await mutation.set_guild_orchestration(gid, profile_key="balanced_helper", actor=_ADMIN)
    d = await orch.resolve(_ctx(gid, chan, cat))
    assert (d.profile_key, d.source) == ("balanced_helper", "guild")

    # Category overrides guild.
    await mutation.set_category_orchestration(gid, cat, profile_key="btd6_grounded", actor=_ADMIN)
    d = await orch.resolve(_ctx(gid, chan, cat))
    assert (d.profile_key, d.source) == ("btd6_grounded", "category")

    # Channel overrides category.
    await mutation.set_channel_orchestration(gid, chan, profile_key="no_tools", actor=_ADMIN)
    d = await orch.resolve(_ctx(gid, chan, cat))
    assert (d.profile_key, d.source) == ("no_tools", "channel")
    assert d.enabled_toolsets == ()  # the real preset narrowed everything away

    # Clearing the channel falls back to the category.
    await mutation.set_channel_orchestration(gid, chan, profile_key=None, actor=_ADMIN)
    d = await orch.resolve(_ctx(gid, chan, cat))
    assert d.source == "category"


async def test_orchestration_only_channel_write_inserts_inherit_mode(postgres_pool) -> None:
    """A channel with no reply-policy row gets mode='inherit' on the orch write."""
    gid = _GUILD_IDS[1]
    chan = 333
    await mutation.set_channel_orchestration(gid, chan, profile_key="btd6_grounded", actor=_ADMIN)
    row = await pool.fetchone(
        """
        SELECT mode, orchestration_profile FROM ai_channel_policy
        WHERE guild_id = $1 AND channel_id = $2
        """,
        (gid, chan),
    )
    assert row is not None
    assert row["mode"] == "inherit"
    assert row["orchestration_profile"] == "btd6_grounded"


async def test_orch_write_preserves_existing_reply_mode(postgres_pool) -> None:
    """Writing an orchestration profile must not clobber an existing NL mode."""
    from services import ai_policy_mutation

    gid = _GUILD_IDS[2]
    chan = 444
    # Establish a reply-policy row with mode='always_reply'.
    await ai_policy_mutation.set_channel_policy(
        gid, chan, mode="always_reply", actor=_ADMIN,
    )
    # Now set an orchestration profile on the same channel.
    await mutation.set_channel_orchestration(gid, chan, profile_key="no_tools", actor=_ADMIN)
    row = await pool.fetchone(
        """
        SELECT mode, orchestration_profile FROM ai_channel_policy
        WHERE guild_id = $1 AND channel_id = $2
        """,
        (gid, chan),
    )
    assert row is not None
    assert row["mode"] == "always_reply"  # reply mode preserved
    assert row["orchestration_profile"] == "no_tools"


async def test_projection_counts(postgres_pool) -> None:
    gid = _GUILD_IDS[3]
    await mutation.set_guild_orchestration(gid, profile_key="balanced_helper", actor=_ADMIN)
    await mutation.set_channel_orchestration(gid, 11, profile_key="btd6_grounded", actor=_ADMIN)
    await mutation.set_channel_orchestration(gid, 12, profile_key="no_tools", actor=_ADMIN)
    await mutation.set_category_orchestration(gid, 21, profile_key="btd6_grounded", actor=_ADMIN)

    snap = await projection.build_snapshot(gid)
    o = snap.orchestration
    assert o.guild_profile_key == "balanced_helper"
    assert o.guild_profile_label == presets.get("balanced_helper").label
    assert o.channel_override_count == 2
    assert o.category_override_count == 1


async def test_generation_bump_invalidates(postgres_pool) -> None:
    gid = _GUILD_IDS[4]
    r1 = await mutation.set_guild_orchestration(gid, profile_key="balanced_helper", actor=_ADMIN)
    d1 = await orch.resolve(_ctx(gid))
    assert d1.profile_key == "balanced_helper"
    r2 = await mutation.set_guild_orchestration(gid, profile_key="no_tools", actor=_ADMIN)
    # The guild setter bumps generation on every write.
    assert r2.generation is not None and r1.generation is not None
    assert r2.generation > r1.generation
    d2 = await orch.resolve(_ctx(gid))
    assert d2.profile_key == "no_tools"  # invalidate() let the new value through
