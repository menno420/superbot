"""Tests for the cleanup-policy operator service (server-management PR9).

Covers the read model (diagnostics), the side-effect-free dry-run preview, and
the audited apply — all with a fake guild + mocked governance seams, so no
Discord or DB is required.  The apply path's guild-scope keying (the PR9
root-cause fix) is pinned here too.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

import services.cleanup_diagnostics as svc
from governance.models import CleanupPolicy, PolicySource

_GID = 789


def _channel(name: str, category_id: int | None = None) -> MagicMock:
    ch = MagicMock()
    ch.name = name
    ch.category_id = category_id
    return ch


def _guild(channels: dict[int, MagicMock] | None = None) -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = _GID
    chans = channels or {}
    guild.get_channel = lambda cid: chans.get(cid)
    return guild


def _row(scope_type, scope_id, inv, failed, after, version=1):
    return {
        "scope_type": scope_type,
        "scope_id": scope_id,
        "delete_invalid_commands": inv,
        "delete_failed_commands": failed,
        "delete_after_seconds": after,
        "policy_version": version,
    }


def _patch_rows(monkeypatch, rows):
    fake_db = MagicMock()
    fake_db.get_all_cleanup_for_guild = AsyncMock(return_value=rows)
    monkeypatch.setattr(svc, "gov_db", fake_db)


def _policy(delete, after, source):
    return CleanupPolicy(
        delete_message=delete,
        delete_after_seconds=after,
        send_feedback=True,
        resolved_from=source,
    )


# ---------------------------------------------------------------------------
# collect_cleanup_diagnostics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_diagnostics_names_levels_and_counts(monkeypatch):
    _patch_rows(
        monkeypatch,
        [
            _row("guild", _GID, True, True, 5),  # Standard
            _row("channel", 111, True, False, 10),  # Light
            _row("channel", 222, True, False, 3),  # Custom (no preset)
        ],
    )
    guild = _guild({111: _channel("general"), 222: _channel("memes")})

    diag = await svc.collect_cleanup_diagnostics(guild)

    by_id = {r.scope_id: r for r in diag.rows}
    assert by_id[_GID].level_name == "Standard"
    assert by_id[111].level_name == "Light"
    assert by_id[222].level_name is None
    assert by_id[222].display_level == "Custom"
    assert diag.total == 3
    assert diag.level_counts == {"Standard": 1, "Light": 1, "Custom": 1}


@pytest.mark.asyncio
async def test_diagnostics_flags_stale_channel(monkeypatch):
    _patch_rows(monkeypatch, [_row("channel", 999, True, True, 5)])
    guild = _guild({})  # channel 999 deleted

    diag = await svc.collect_cleanup_diagnostics(guild)

    assert len(diag.stale_rows) == 1
    stale = diag.stale_rows[0]
    assert stale.is_stale is True
    assert "deleted" in stale.target_label


@pytest.mark.asyncio
async def test_diagnostics_flags_ineffective_legacy_guild_row(monkeypatch):
    """A guild row keyed by 0 (the legacy bug) is flagged ineffective."""
    _patch_rows(monkeypatch, [_row("guild", 0, True, True, 5)])
    guild = _guild({})

    diag = await svc.collect_cleanup_diagnostics(guild)

    assert len(diag.ineffective_rows) == 1
    assert diag.ineffective_rows[0].is_ineffective is True


@pytest.mark.asyncio
async def test_diagnostics_guild_row_at_guild_id_is_effective(monkeypatch):
    _patch_rows(monkeypatch, [_row("guild", _GID, True, True, 5)])
    diag = await svc.collect_cleanup_diagnostics(_guild({}))
    assert diag.ineffective_rows == ()


@pytest.mark.asyncio
async def test_diagnostics_orders_guild_then_category_then_channel(monkeypatch):
    _patch_rows(
        monkeypatch,
        [
            _row("channel", 111, True, True, 5),
            _row("guild", _GID, True, True, 5),
            _row("category", 50, True, True, 5),
        ],
    )
    guild = _guild({111: _channel("c"), 50: _channel("cat")})
    diag = await svc.collect_cleanup_diagnostics(guild)
    assert [r.scope_type for r in diag.rows] == ["guild", "category", "channel"]


# ---------------------------------------------------------------------------
# preview_cleanup_change (dry-run)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_detects_effect_change(monkeypatch):
    # Currently inherits Off-ish (no delete); previewing Strict (delete, 2s).
    monkeypatch.setattr(
        svc,
        "resolve_cleanup_policy",
        AsyncMock(return_value=_policy(False, 0, PolicySource.FALLBACK_DEFAULT)),
    )
    guild = _guild({111: _channel("general", category_id=None)})

    preview = await svc.preview_cleanup_change(guild, "channel", 111, "Strict")

    assert preview.new_delete_message is True
    assert preview.new_delete_after_seconds == 2
    assert preview.will_change is True
    assert preview.current_source == PolicySource.FALLBACK_DEFAULT


@pytest.mark.asyncio
async def test_preview_same_effect_but_pins_source_is_a_change(monkeypatch):
    # Channel currently resolves Standard via the GUILD default (inherited).
    monkeypatch.setattr(
        svc,
        "resolve_cleanup_policy",
        AsyncMock(return_value=_policy(True, 5, PolicySource.GUILD_OVERRIDE)),
    )
    guild = _guild({111: _channel("general")})

    preview = await svc.preview_cleanup_change(guild, "channel", 111, "Standard")

    # Same effect (delete=True/5s) but it pins an explicit channel override.
    assert preview.will_change is True
    assert any("pins an explicit override" in w for w in preview.warnings)


@pytest.mark.asyncio
async def test_preview_no_change_when_same_override_present(monkeypatch):
    # Channel already has its own Standard override.
    monkeypatch.setattr(
        svc,
        "resolve_cleanup_policy",
        AsyncMock(return_value=_policy(True, 5, PolicySource.CHANNEL_OVERRIDE)),
    )
    guild = _guild({111: _channel("general")})

    preview = await svc.preview_cleanup_change(guild, "channel", 111, "Standard")

    assert preview.will_change is False


@pytest.mark.asyncio
async def test_preview_warns_on_stale_scope(monkeypatch):
    monkeypatch.setattr(
        svc,
        "resolve_cleanup_policy",
        AsyncMock(return_value=_policy(True, 5, PolicySource.GUILD_OVERRIDE)),
    )
    guild = _guild({})  # channel 999 deleted

    preview = await svc.preview_cleanup_change(guild, "channel", 999, "Light")

    assert any("no longer exists" in w for w in preview.warnings)


@pytest.mark.asyncio
async def test_preview_writes_nothing(monkeypatch):
    """Dry-run must never call the write path."""
    monkeypatch.setattr(
        svc,
        "resolve_cleanup_policy",
        AsyncMock(return_value=_policy(True, 5, PolicySource.GUILD_OVERRIDE)),
    )
    writer = AsyncMock()
    monkeypatch.setattr(svc, "set_cleanup_policy_for_scope", writer)

    await svc.preview_cleanup_change(_guild({111: _channel("g")}), "channel", 111, "Off")

    writer.assert_not_called()


# ---------------------------------------------------------------------------
# apply_cleanup_change
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_guild_scope_keys_on_guild_id(monkeypatch):
    """The root-cause fix: guild apply writes scope_id=guild_id, not 0."""
    writer = AsyncMock()
    monkeypatch.setattr(svc, "set_cleanup_policy_for_scope", writer)
    member = MagicMock(spec=discord.Member)

    await svc.apply_cleanup_change(_guild({}), member, "guild", None, "Standard")

    writer.assert_awaited_once()
    ctx_arg, scope_type, scope_id = writer.await_args.args
    assert scope_type == "guild"
    assert scope_id == _GID  # guild_id, not 0
    assert ctx_arg.guild_id == _GID
    assert ctx_arg.member is member
    kwargs = writer.await_args.kwargs
    assert kwargs["delete_invalid_commands"] is True
    assert kwargs["delete_failed_commands"] is True
    assert kwargs["delete_after_seconds"] == 5


@pytest.mark.asyncio
async def test_apply_channel_scope_passes_snowflake(monkeypatch):
    writer = AsyncMock()
    monkeypatch.setattr(svc, "set_cleanup_policy_for_scope", writer)
    member = MagicMock(spec=discord.Member)

    await svc.apply_cleanup_change(_guild({}), member, "channel", 555, "Off")

    _ctx, scope_type, scope_id = writer.await_args.args
    assert scope_type == "channel"
    assert scope_id == 555
    assert writer.await_args.kwargs["delete_after_seconds"] == 0


@pytest.mark.asyncio
async def test_apply_rejects_thread_scope(monkeypatch):
    writer = AsyncMock()
    monkeypatch.setattr(svc, "set_cleanup_policy_for_scope", writer)
    with pytest.raises(ValueError, match="thread"):
        await svc.apply_cleanup_change(
            _guild({}), MagicMock(spec=discord.Member), "thread", 1, "Off",
        )
    writer.assert_not_called()


@pytest.mark.asyncio
async def test_apply_rejects_unknown_level(monkeypatch):
    writer = AsyncMock()
    monkeypatch.setattr(svc, "set_cleanup_policy_for_scope", writer)
    with pytest.raises(ValueError, match="level"):
        await svc.apply_cleanup_change(
            _guild({}), MagicMock(spec=discord.Member), "guild", None, "Nuclear",
        )
    writer.assert_not_called()
