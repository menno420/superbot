"""Gating + source-toggle behavior for the BTD6 ops cog.

Pins the mixed authorization model:
- readiness/runs are staff-gated (manage_guild OR administrator),
- source enable/disable are administrator-gated, matching
  ``btd6_source_mutation._check_admin`` — and both the NULL-base_url and
  unauthorized failure modes surface as friendly lines.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.btd6_ops_cog import (
    _ADMIN_DENIED,
    _STAFF_DENIED,
    BTD6OpsCog,
    _toggle_source,
)


def _actor(*, administrator: bool = False, manage_guild: bool = False) -> SimpleNamespace:
    perms = SimpleNamespace(administrator=administrator, manage_guild=manage_guild)
    return SimpleNamespace(id=123, guild_permissions=perms)


# ---------------------------------------------------------------------------
# _toggle_source — error-path mapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_toggle_source_success(monkeypatch) -> None:
    from services import btd6_source_mutation

    async def _set_enabled(key, *, enabled, actor, reason):
        return SimpleNamespace(source_key=key, action="enabled")

    monkeypatch.setattr(btd6_source_mutation, "set_enabled", _set_enabled)
    msg = await _toggle_source(_actor(administrator=True), "nk_x", enabled=True)
    assert "✅" in msg
    assert "nk_x" in msg
    assert "enabled" in msg


@pytest.mark.asyncio
async def test_toggle_source_null_base_url_is_friendly(monkeypatch) -> None:
    from services import btd6_source_mutation

    async def _set_enabled(key, *, enabled, actor, reason):
        raise btd6_source_mutation.InvalidSourceValueError(
            "refusing to enable 'nk_x': base_url is NULL",
        )

    monkeypatch.setattr(btd6_source_mutation, "set_enabled", _set_enabled)
    msg = await _toggle_source(_actor(administrator=True), "nk_x", enabled=True)
    assert "⚠️" in msg
    assert "base_url" in msg


@pytest.mark.asyncio
async def test_toggle_source_unauthorized_maps_to_admin_denied(monkeypatch) -> None:
    from services import btd6_source_mutation

    async def _set_enabled(key, *, enabled, actor, reason):
        raise btd6_source_mutation.UnauthorizedSourceMutationError("nope")

    monkeypatch.setattr(btd6_source_mutation, "set_enabled", _set_enabled)
    msg = await _toggle_source(_actor(), "nk_x", enabled=True)
    assert msg == _ADMIN_DENIED


# ---------------------------------------------------------------------------
# Command-callback gating
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_readiness_prefix_denies_non_staff() -> None:
    cog = BTD6OpsCog(bot=MagicMock())
    ctx = MagicMock()
    ctx.author = _actor()  # no perms
    ctx.send = AsyncMock()
    await BTD6OpsCog.readiness_prefix.callback(cog, ctx)
    ctx.send.assert_awaited_once_with(_STAFF_DENIED)


@pytest.mark.asyncio
async def test_readiness_prefix_allows_staff(monkeypatch) -> None:
    import discord

    from cogs import btd6_ops_cog

    async def _embed():
        return discord.Embed(title="ready")

    monkeypatch.setattr(btd6_ops_cog, "_readiness_embed", _embed)
    cog = BTD6OpsCog(bot=MagicMock())
    ctx = MagicMock()
    ctx.author = _actor(manage_guild=True)
    ctx.send = AsyncMock()
    await BTD6OpsCog.readiness_prefix.callback(cog, ctx)
    ctx.send.assert_awaited_once()
    assert "embed" in ctx.send.await_args.kwargs


@pytest.mark.asyncio
async def test_source_enable_prefix_denies_staff_non_admin() -> None:
    cog = BTD6OpsCog(bot=MagicMock())
    ctx = MagicMock()
    ctx.author = _actor(manage_guild=True)  # staff, but not administrator
    ctx.send = AsyncMock()
    await BTD6OpsCog.source_enable_prefix.callback(cog, ctx, "nk_x")
    ctx.send.assert_awaited_once_with(_ADMIN_DENIED)


@pytest.mark.asyncio
async def test_source_enable_prefix_allows_admin(monkeypatch) -> None:
    from cogs import btd6_ops_cog

    async def _toggle(actor, key, *, enabled):
        return f"✅ Source `{key}` enabled."

    monkeypatch.setattr(btd6_ops_cog, "_toggle_source", _toggle)
    cog = BTD6OpsCog(bot=MagicMock())
    ctx = MagicMock()
    ctx.author = _actor(administrator=True)
    ctx.send = AsyncMock()
    await BTD6OpsCog.source_enable_prefix.callback(cog, ctx, "nk_x")
    ctx.send.assert_awaited_once()
    assert "✅" in ctx.send.await_args.args[0]
