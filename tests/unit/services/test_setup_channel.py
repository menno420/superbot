"""Tests for ``services.setup_channel`` — auto-created private setup channel."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_channel import (
    SETUP_CHANNEL_NAME,
    ensure_setup_channel,
)
from services.setup_session import SetupSession


def _session(
    *,
    guild_id: int = 1,
    delegated_admins: tuple[int, ...] = (),
    setup_channel_id: int | None = None,
) -> SetupSession:
    return SetupSession(
        guild_id=guild_id,
        guild_name="Test",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=setup_channel_id,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=delegated_admins,
        skipped_sections=frozenset(),
        depth=None,
    )


def _make_guild(
    *,
    guild_id: int = 1,
    can_manage_channels: bool = True,
    me_present: bool = True,
    owner_present: bool = True,
    cached_channel: discord.TextChannel | None = None,
    roles: list | None = None,
    delegated_members: dict[int, discord.Member] | None = None,
):
    g = MagicMock(spec=discord.Guild)
    g.id = guild_id
    g.name = "Test"

    if me_present:
        me = MagicMock()
        me.guild_permissions = SimpleNamespace(manage_channels=can_manage_channels)
        g.me = me
    else:
        g.me = None

    if owner_present:
        g.owner = MagicMock()
        g.owner.mention = "<@99>"
    else:
        g.owner = None

    default_role = MagicMock()
    default_role.id = 0
    g.default_role = default_role
    g.roles = roles if roles is not None else [default_role]
    g.get_channel = MagicMock(
        return_value=cached_channel if cached_channel is not None else None,
    )
    delegated_members = delegated_members or {}
    g.get_member = MagicMock(side_effect=lambda uid: delegated_members.get(uid))
    return g


def _make_role(
    *,
    role_id: int,
    administrator: bool,
    name: str = "role",
) -> MagicMock:
    role = MagicMock(spec=discord.Role)
    role.id = role_id
    role.name = name
    role.permissions = SimpleNamespace(administrator=administrator)
    return role


def _make_member(member_id: int) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = member_id
    return member


def _make_text_channel(channel_id: int = 7000):
    ch = MagicMock(spec=discord.TextChannel)
    ch.id = channel_id
    ch.name = SETUP_CHANNEL_NAME
    return ch


@pytest.mark.asyncio
async def test_ensure_setup_channel_creates_when_missing():
    guild = _make_guild()
    created = _make_text_channel(7000)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=created,
    ) as ensure_mock:
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is created
    assert was_created is True
    ensure_mock.assert_awaited_once()
    kwargs = ensure_mock.await_args.kwargs
    assert kwargs["kind"] == "text"


@pytest.mark.asyncio
async def test_ensure_setup_channel_reuses_cached_id():
    """When the caller supplies the prior ``existing_channel_id`` and the
    guild still has that channel, no creation attempt is made."""
    cached = _make_text_channel(7000)
    guild = _make_guild(cached_channel=cached)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
    ) as ensure_mock:
        channel, was_created = await ensure_setup_channel(
            guild,
            existing_channel_id=7000,
        )

    assert channel is cached
    assert was_created is False
    ensure_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_setup_channel_returns_none_when_no_manage_channels():
    """Without Manage Channels the bot cannot create; falls back to caller."""
    guild = _make_guild(can_manage_channels=False)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
    ) as ensure_mock:
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False
    ensure_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_setup_channel_returns_none_when_me_missing():
    """``guild.me`` may be ``None`` for guilds not yet fully resolved."""
    guild = _make_guild(me_present=False)

    channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False


@pytest.mark.asyncio
async def test_ensure_setup_channel_handles_forbidden_gracefully():
    guild = _make_guild()

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        side_effect=discord.Forbidden(MagicMock(), "manage_channels missing"),
    ):
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False


@pytest.mark.asyncio
async def test_ensure_setup_channel_handles_http_error_gracefully():
    guild = _make_guild()

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        side_effect=discord.HTTPException(MagicMock(), "boom"),
    ):
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False


@pytest.mark.asyncio
async def test_ensure_setup_channel_returns_none_when_helper_yields_non_text():
    """If ``ensure_channel`` somehow returns a voice/category we refuse."""
    guild = _make_guild()
    bad = MagicMock(spec=discord.VoiceChannel)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=bad,
    ):
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False


@pytest.mark.asyncio
async def test_ensure_setup_channel_passes_private_overwrites():
    """The ``overwrites`` dict denies @everyone view and grants the bot."""
    guild = _make_guild()
    created = _make_text_channel(7000)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=created,
    ) as ensure_mock:
        await ensure_setup_channel(guild)

    overwrites = ensure_mock.await_args.kwargs["overwrites"]
    # @everyone (default_role) must be present with view denied
    assert guild.default_role in overwrites
    default_overwrite = overwrites[guild.default_role]
    assert default_overwrite.view_channel is False
    # Bot must be granted access
    assert guild.me in overwrites
    # Owner must be granted access when present
    assert guild.owner in overwrites


# ---------------------------------------------------------------------------
# Phase 1 — admin-role denial, delegated-admin allow, recompute on reuse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_setup_channel_denies_administrator_roles_explicitly():
    """Roles with the administrator permission are denied view_channel
    explicitly so an audit reading the overwrite set sees the intent.
    """
    admin_role = _make_role(role_id=100, administrator=True, name="Admin")
    non_admin_role = _make_role(role_id=200, administrator=False, name="Member")
    guild = _make_guild(roles=[_make_role(role_id=0, administrator=False), admin_role, non_admin_role])
    # default_role id must match the one we passed
    guild.default_role = guild.roles[0]
    created = _make_text_channel(7000)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=created,
    ) as ensure_mock:
        await ensure_setup_channel(guild)

    overwrites = ensure_mock.await_args.kwargs["overwrites"]
    assert admin_role in overwrites
    assert overwrites[admin_role].view_channel is False
    # Non-admin roles do NOT get an explicit overwrite — they fall
    # through @everyone's denial.
    assert non_admin_role not in overwrites


@pytest.mark.asyncio
async def test_ensure_setup_channel_grants_delegated_admins_explicit_access():
    delegate = _make_member(42)
    guild = _make_guild(delegated_members={42: delegate})
    session = _session(delegated_admins=(42,))
    created = _make_text_channel(7000)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=created,
    ) as ensure_mock:
        await ensure_setup_channel(guild, session=session)

    overwrites = ensure_mock.await_args.kwargs["overwrites"]
    assert delegate in overwrites
    grant = overwrites[delegate]
    assert grant.view_channel is True
    assert grant.send_messages is True


@pytest.mark.asyncio
async def test_ensure_setup_channel_skips_delegated_admins_who_left_guild():
    """A delegated id that doesn't resolve to a current member is
    skipped silently — they may have left the guild.  The session row
    keeps the id for the next recompute when they rejoin.
    """
    # delegated_members map has no entry for id 42
    guild = _make_guild(delegated_members={})
    session = _session(delegated_admins=(42,))
    created = _make_text_channel(7000)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=created,
    ) as ensure_mock:
        await ensure_setup_channel(guild, session=session)

    overwrites = ensure_mock.await_args.kwargs["overwrites"]
    member_ids = [getattr(k, "id", None) for k in overwrites]
    assert 42 not in member_ids


@pytest.mark.asyncio
async def test_ensure_setup_channel_recomputes_overwrites_on_cached_reuse():
    """When the cached channel id resolves, overwrites are still
    re-applied so admin-role denials and delegate grants follow the
    latest membership snapshot.  Pre-Phase 1 this was a silent
    no-op.
    """
    delegate = _make_member(42)
    cached = _make_text_channel(7000)
    cached.edit = AsyncMock()
    guild = _make_guild(cached_channel=cached, delegated_members={42: delegate})
    session = _session(delegated_admins=(42,))

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
    ) as ensure_mock:
        channel, was_created = await ensure_setup_channel(
            guild,
            existing_channel_id=7000,
            session=session,
        )

    # The create path is not invoked because the channel was cached.
    ensure_mock.assert_not_called()
    assert channel is cached
    assert was_created is False
    # But edit() WAS called to recompute overwrites.
    cached.edit.assert_awaited_once()
    edit_kwargs = cached.edit.await_args.kwargs
    overwrites = edit_kwargs["overwrites"]
    assert delegate in overwrites
    assert overwrites[delegate].view_channel is True


@pytest.mark.asyncio
async def test_ensure_setup_channel_recompute_on_reuse_is_idempotent():
    """Recompute on reuse can run repeatedly without error or duplicate
    side effects beyond a single edit per call.
    """
    delegate = _make_member(42)
    cached = _make_text_channel(7000)
    cached.edit = AsyncMock()
    guild = _make_guild(cached_channel=cached, delegated_members={42: delegate})
    session = _session(delegated_admins=(42,))

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
    ):
        for _ in range(3):
            await ensure_setup_channel(
                guild,
                existing_channel_id=7000,
                session=session,
            )

    # One edit per call — no batching, no skipping.
    assert cached.edit.await_count == 3


@pytest.mark.asyncio
async def test_recompute_setup_channel_overwrites_uses_session_channel_id():
    from services.setup_channel import recompute_setup_channel_overwrites

    cached = _make_text_channel(7000)
    cached.edit = AsyncMock()
    guild = _make_guild(cached_channel=cached)
    session = _session(setup_channel_id=7000)

    ok = await recompute_setup_channel_overwrites(guild, session)
    assert ok is True
    cached.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_recompute_setup_channel_overwrites_returns_false_when_unresolvable():
    """No channel id, no explicit channel arg, no recompute possible."""
    from services.setup_channel import recompute_setup_channel_overwrites

    guild = _make_guild(cached_channel=None)
    session = _session(setup_channel_id=None)

    ok = await recompute_setup_channel_overwrites(guild, session)
    assert ok is False


@pytest.mark.asyncio
async def test_recompute_setup_channel_overwrites_with_explicit_channel():
    """An explicit channel arg bypasses the session.setup_channel_id lookup."""
    from services.setup_channel import recompute_setup_channel_overwrites

    cached = _make_text_channel(7000)
    cached.edit = AsyncMock()
    guild = _make_guild(cached_channel=None)
    session = _session(setup_channel_id=None)

    ok = await recompute_setup_channel_overwrites(
        guild,
        session,
        channel=cached,
    )
    assert ok is True
    cached.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_recompute_setup_channel_overwrites_handles_forbidden():
    """A Forbidden during edit returns False but does not raise."""
    from services.setup_channel import recompute_setup_channel_overwrites

    cached = _make_text_channel(7000)
    cached.edit = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(), "denied"),
    )
    guild = _make_guild(cached_channel=cached)
    session = _session(setup_channel_id=7000)

    ok = await recompute_setup_channel_overwrites(guild, session)
    assert ok is False


def test_privacy_note_is_exported_and_mentions_interaction_checks():
    from services.setup_channel import PRIVACY_NOTE

    text = PRIVACY_NOTE.lower()
    assert "admins" in text
    assert "interaction checks" in text


# ---------------------------------------------------------------------------
# delete_setup_channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_setup_channel_succeeds_when_name_matches():
    from services.setup_channel import delete_setup_channel

    tracked = _make_text_channel(channel_id=7000)
    tracked.delete = AsyncMock()
    guild = _make_guild(cached_channel=tracked)

    ok = await delete_setup_channel(guild, 7000)
    assert ok is True
    tracked.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_setup_channel_refuses_renamed_channel():
    """If an operator renamed the channel we treat it as no longer
    bot-managed and decline to delete it."""
    from services.setup_channel import delete_setup_channel

    tracked = _make_text_channel(channel_id=7000)
    tracked.name = "renamed-by-operator"
    tracked.delete = AsyncMock()
    guild = _make_guild(cached_channel=tracked)

    ok = await delete_setup_channel(guild, 7000)
    assert ok is False
    tracked.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_setup_channel_returns_true_when_already_gone():
    """A channel that has already been deleted (cache miss) is
    treated as success so the caller can move on."""
    from services.setup_channel import delete_setup_channel

    guild = _make_guild(cached_channel=None)
    ok = await delete_setup_channel(guild, 9999)
    assert ok is True


@pytest.mark.asyncio
async def test_delete_setup_channel_returns_true_on_not_found_during_delete():
    """A race where Discord reports NotFound during the delete is
    also treated as success."""
    from services.setup_channel import delete_setup_channel

    tracked = _make_text_channel(channel_id=7000)
    tracked.delete = AsyncMock(
        side_effect=discord.NotFound(MagicMock(), "gone"),
    )
    guild = _make_guild(cached_channel=tracked)

    ok = await delete_setup_channel(guild, 7000)
    assert ok is True


@pytest.mark.asyncio
async def test_delete_setup_channel_returns_false_on_forbidden():
    from services.setup_channel import delete_setup_channel

    tracked = _make_text_channel(channel_id=7000)
    tracked.delete = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(), "missing manage_channels"),
    )
    guild = _make_guild(cached_channel=tracked)

    ok = await delete_setup_channel(guild, 7000)
    assert ok is False
