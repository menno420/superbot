"""F-1 caching tests for the XP listener (S2.2).

Asserts that:
  * the on_message hot path serves XP config from the F-1 cache (one
    DB read per (guild, key) over a window of messages),
  * admin write paths invalidate the cache so the next read picks up
    the new value,
  * the threshold-roles cache invalidates on every role-threshold
    mutation site.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime import guild_config


@pytest.fixture(autouse=True)
def _reset_cache():
    guild_config._reset_for_tests()
    yield
    guild_config._reset_for_tests()


def _make_message(*, guild_id: int = 99, user_id: int = 1) -> MagicMock:
    msg = MagicMock()
    msg.author = MagicMock()
    msg.author.bot = False
    msg.author.id = user_id
    msg.guild = MagicMock()
    msg.guild.id = guild_id
    return msg


def _xp_settings_replies(get_setting: AsyncMock, *, min_=15, max_=25, cd=60, ann=""):
    """Side-effect that mimics db.get_setting reading the 4 XP keys."""

    async def reply(guild_id, key, default=""):  # noqa: ARG001 — signature parity
        return {
            "xp_min": str(min_),
            "xp_max": str(max_),
            "xp_cooldown": str(cd),
            "xp_announce_channel": ann,
        }.get(key, default)

    get_setting.side_effect = reply


# ---------------------------------------------------------------------------
# Hot-path caching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_message_calls_db_get_setting_at_most_once_per_guild_over_a_window():
    """Five rapid messages from the same guild → one cache fill, then hits."""
    from cogs.xp_cog import XpCog

    cog = XpCog(bot=MagicMock())
    message = _make_message()
    db_row = {"last_xp": 0, "messages": 1}

    with (
        patch(
            "cogs.xp.listener.db.get_xp", new_callable=AsyncMock, return_value=db_row
        ),
        patch(
            "utils.guild_config_accessors.db.get_setting",
            new_callable=AsyncMock,
        ) as get_setting,
        patch("cogs.xp.listener.check_cooldown", return_value=(True, 0)),
    ):
        _xp_settings_replies(get_setting)
        for _ in range(5):
            await cog.on_message(message)

    # Cache fill reads each of 4 keys exactly once on the first message;
    # subsequent 4 messages all hit the cache → no further DB reads.
    assert get_setting.await_count == 4


@pytest.mark.asyncio
async def test_on_message_caches_per_guild_independently():
    """Two guilds → 8 DB reads (4 per guild), not 4 (no cross-guild collision)."""
    from cogs.xp_cog import XpCog

    cog = XpCog(bot=MagicMock())
    db_row = {"last_xp": 0, "messages": 1}

    with (
        patch(
            "cogs.xp.listener.db.get_xp", new_callable=AsyncMock, return_value=db_row
        ),
        patch(
            "utils.guild_config_accessors.db.get_setting",
            new_callable=AsyncMock,
        ) as get_setting,
        patch("cogs.xp.listener.check_cooldown", return_value=(True, 0)),
    ):
        _xp_settings_replies(get_setting)
        await cog.on_message(_make_message(guild_id=1))
        await cog.on_message(_make_message(guild_id=2))
        await cog.on_message(_make_message(guild_id=1))  # cached
        await cog.on_message(_make_message(guild_id=2))  # cached

    assert get_setting.await_count == 8  # 4 per guild × 2 guilds


# ---------------------------------------------------------------------------
# Invalidation on admin write paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_xp_config_forces_reload_on_next_read():
    """After invalidation, the next get_xp_config call re-runs the loader."""
    from utils.guild_config_accessors import get_xp_config, invalidate_xp_config

    with patch(
        "utils.guild_config_accessors.db.get_setting",
        new_callable=AsyncMock,
    ) as get_setting:
        _xp_settings_replies(get_setting, min_=10)
        first = await get_xp_config(42)
        assert first.xp_min == 10
        await get_xp_config(42)  # cached
        assert get_setting.await_count == 4

        # Simulate an admin write: new value in DB + explicit invalidation.
        _xp_settings_replies(get_setting, min_=99)
        invalidate_xp_config(42)

        second = await get_xp_config(42)
        assert second.xp_min == 99
        assert get_setting.await_count == 8  # 4 more reads on the reload


@pytest.mark.asyncio
async def test_invalidate_xp_threshold_roles_forces_reload_on_next_read():
    """Same shape for the threshold-roles accessor."""
    from utils.guild_config_accessors import (
        get_xp_threshold_roles,
        invalidate_xp_threshold_roles,
    )

    payloads = [
        [{"role_name": "veteran", "level_required": 5}],
        [{"role_name": "veteran", "level_required": 10}],
    ]
    with patch(
        "utils.guild_config_accessors.db.get_xp_threshold_roles",
        new_callable=AsyncMock,
        side_effect=payloads + payloads,  # extras safe-guard
    ) as fetch:
        first = await get_xp_threshold_roles(7)
        await get_xp_threshold_roles(7)  # cached
        assert fetch.await_count == 1
        assert first[0]["level_required"] == 5

        invalidate_xp_threshold_roles(7)

        second = await get_xp_threshold_roles(7)
        assert fetch.await_count == 2
        assert second[0]["level_required"] == 10


# ---------------------------------------------------------------------------
# Static wiring checks — every mutation site that affects the XP-config or
# threshold-roles cache must import the invalidator.  If the import is
# absent the runtime cache will go stale on that path.
# ---------------------------------------------------------------------------


def test_xp_cog_imports_invalidate_xp_config():
    """xp_cog must import the XP-config invalidator for its 3 admin modals."""
    import cogs.xp_cog as xp_cog

    assert hasattr(xp_cog, "invalidate_xp_config"), (
        "xp_cog.py is missing `from utils.guild_config_accessors import "
        "invalidate_xp_config` — the 3 admin XP-setting modals will go stale."
    )


@pytest.mark.parametrize(
    "module_path",
    [
        "views.roles.xp_roles_panel",
        "views.roles.creation_panel",
        "views.roles.time_roles_panel",
        "cogs.role_cog",
    ],
)
def test_threshold_role_mutation_sites_import_invalidator(module_path):
    """Every module that mutates ``role_thresholds`` rows that affect
    ``get_xp_threshold_roles`` must import the cache invalidator.
    """
    import importlib

    mod = importlib.import_module(module_path)
    assert hasattr(mod, "invalidate_xp_threshold_roles"), (
        f"{module_path} mutates role_thresholds but does not import "
        f"`invalidate_xp_threshold_roles` — its writes will not invalidate "
        f"the F-1 cache and on_message will see stale XP-role thresholds."
    )
