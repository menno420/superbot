"""Unit tests for the S7b logging binding-select flow.

Covers:

- :class:`LogChannelSelectView` shape (ChannelSelect + Clear button,
  invoker-locked).
- The select callback routes through
  :class:`BindingMutationPipeline.set_binding` with the correct
  ``subsystem`` / ``binding_name`` / ``kind`` / ``target_id`` /
  ``actor``.
- The clear button routes through
  :class:`BindingMutationPipeline.clear_binding`.
- Pipeline failure surfaces as an ephemeral error embed.
- DM invocation (no guild) is rejected with a clear message.

The S7b update to :func:`services.server_logging.resolve_log_channel`
is covered by additional tests in
``tests/unit/services/test_server_logging.py``; here we exercise the
binding-first resolution explicitly so the new code path has direct
coverage.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.logging.select_view import LogChannelSelectView
from core.runtime.subsystem_schema import BindingKind


def _author(id_: int = 1) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = id_
    return member


def _text_channel(id_: int = 100) -> MagicMock:
    ch = MagicMock(spec=discord.TextChannel)
    ch.id = id_
    ch.mention = f"<#{id_}>"
    return ch


def _interaction(*, author: MagicMock, guild: object) -> MagicMock:
    interaction = MagicMock()
    interaction.user = author
    interaction.guild = guild
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_channel_select_and_clear_button():
    view = LogChannelSelectView(_author(), "mod")
    selects = [c for c in view.children if isinstance(c, discord.ui.ChannelSelect)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert len(buttons) == 1
    assert "Clear" in (buttons[0].label or "")


def test_view_channel_select_restricted_to_text_channels():
    view = LogChannelSelectView(_author(), "cleanup")
    sel = next(c for c in view.children if isinstance(c, discord.ui.ChannelSelect))
    assert discord.ChannelType.text in sel.channel_types


def test_view_kind_unknown_raises():
    """A typo in kind must fail fast at construction time."""
    with pytest.raises(ValueError):
        LogChannelSelectView(_author(), "garbage")


@pytest.mark.asyncio
async def test_view_invoker_check_rejects_other_user():
    view = LogChannelSelectView(_author(id_=42), "mod")
    interaction = MagicMock()
    interaction.user.id = 99
    interaction.response.send_message = AsyncMock()
    result = await view.interaction_check(interaction)
    assert result is False
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Select callback — routes through BindingMutationPipeline.set_binding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_select_callback_writes_via_binding_pipeline_for_mod():
    actor = _author()
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    target = _text_channel(id_=500)
    interaction = _interaction(author=actor, guild=guild)

    fake_result = MagicMock()
    fake_result.new_status.value = "ok"
    fake_pipeline = MagicMock()
    fake_pipeline.set_binding = AsyncMock(return_value=fake_result)

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=fake_pipeline,
    ):
        from cogs.logging.select_view import _commit_selection

        await _commit_selection(interaction, kind="mod", target=target)

    fake_pipeline.set_binding.assert_awaited_once_with(
        guild=guild,
        subsystem="logging",
        binding_name="mod_channel",
        kind=BindingKind.CHANNEL,
        target_id=500,
        actor=actor,
    )


@pytest.mark.asyncio
async def test_select_callback_writes_via_binding_pipeline_for_cleanup():
    actor = _author()
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    target = _text_channel(id_=600)
    interaction = _interaction(author=actor, guild=guild)

    fake_result = MagicMock()
    fake_result.new_status.value = "ok"
    fake_pipeline = MagicMock()
    fake_pipeline.set_binding = AsyncMock(return_value=fake_result)

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=fake_pipeline,
    ):
        from cogs.logging.select_view import _commit_selection

        await _commit_selection(interaction, kind="cleanup", target=target)

    fake_pipeline.set_binding.assert_awaited_once_with(
        guild=guild,
        subsystem="logging",
        binding_name="cleanup_channel",
        kind=BindingKind.CHANNEL,
        target_id=600,
        actor=actor,
    )


@pytest.mark.asyncio
async def test_select_callback_rejects_dm_invocation():
    interaction = _interaction(author=_author(), guild=None)

    from cogs.logging.select_view import _commit_selection

    await _commit_selection(interaction, kind="mod", target=_text_channel())
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "guild context" in msg


@pytest.mark.asyncio
async def test_select_callback_surfaces_pipeline_error_ephemerally():
    """A BindingMutationError must produce an ephemeral message; the
    view must not crash and must not silently swallow the failure."""
    from services.binding_mutation import BindingMutationError

    actor = _author()
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    interaction = _interaction(author=actor, guild=guild)

    fake_pipeline = MagicMock()
    fake_pipeline.set_binding = AsyncMock(
        side_effect=BindingMutationError("kind mismatch"),
    )

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=fake_pipeline,
    ):
        from cogs.logging.select_view import _commit_selection

        await _commit_selection(interaction, kind="mod", target=_text_channel())

    interaction.response.send_message.assert_awaited_once()
    sent = interaction.response.send_message.await_args
    assert sent.kwargs.get("ephemeral") is True
    msg = sent.args[0]
    assert "BindingMutationError" in msg


# ---------------------------------------------------------------------------
# Clear callback — routes through clear_binding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_callback_routes_through_clear_binding():
    actor = _author()
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    interaction = _interaction(author=actor, guild=guild)

    fake_pipeline = MagicMock()
    fake_pipeline.clear_binding = AsyncMock(return_value=MagicMock())

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=fake_pipeline,
    ):
        from cogs.logging.select_view import _commit_clear

        await _commit_clear(interaction, kind="cleanup")

    fake_pipeline.clear_binding.assert_awaited_once_with(
        guild=guild,
        subsystem="logging",
        binding_name="cleanup_channel",
        kind=BindingKind.CHANNEL,
        actor=actor,
    )


@pytest.mark.asyncio
async def test_clear_callback_rejects_dm_invocation():
    interaction = _interaction(author=_author(), guild=None)

    from cogs.logging.select_view import _commit_clear

    await _commit_clear(interaction, kind="mod")
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "guild context" in msg


# ---------------------------------------------------------------------------
# resolve_log_channel — binding-first resolution (the S7b service change)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_log_channel_prefers_binding_over_legacy():
    """When the binding is set, it wins over the legacy scalar key."""
    from services.server_logging import resolve_log_channel

    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    bound_channel = MagicMock(spec=discord.TextChannel)
    guild.get_channel = MagicMock(return_value=bound_channel)

    bound_binding = MagicMock()
    bound_binding.target_id = 42

    with (
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=bound_binding,
        ),
        patch(
            "core.runtime.guild_resources.resolve_settings_channel",
            new_callable=AsyncMock,
            return_value=MagicMock(spec=discord.TextChannel),  # legacy also set
        ),
    ):
        result = await resolve_log_channel(guild, "mod")
    assert result is bound_channel
    guild.get_channel.assert_called_with(42)


@pytest.mark.asyncio
async def test_resolve_log_channel_falls_back_to_legacy_when_binding_unset():
    from services.server_logging import resolve_log_channel

    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    legacy_channel = MagicMock(spec=discord.TextChannel)

    unbound = MagicMock()
    unbound.target_id = None

    with (
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=unbound,
        ),
        patch(
            "core.runtime.guild_resources.resolve_settings_channel",
            new_callable=AsyncMock,
            return_value=legacy_channel,
        ),
    ):
        result = await resolve_log_channel(guild, "mod")
    assert result is legacy_channel


@pytest.mark.asyncio
async def test_resolve_log_channel_falls_back_to_legacy_when_binding_target_missing():
    """If the binding's target_id no longer exists in the guild, fall through."""
    from services.server_logging import resolve_log_channel

    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    guild.get_channel = MagicMock(return_value=None)  # binding target missing
    legacy_channel = MagicMock(spec=discord.TextChannel)

    bound_to_missing = MagicMock()
    bound_to_missing.target_id = 999

    with (
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=bound_to_missing,
        ),
        patch(
            "core.runtime.guild_resources.resolve_settings_channel",
            new_callable=AsyncMock,
            return_value=legacy_channel,
        ),
    ):
        result = await resolve_log_channel(guild, "mod")
    assert result is legacy_channel


@pytest.mark.asyncio
async def test_resolve_log_channel_cleanup_falls_back_to_mod_binding():
    """When cleanup binding + legacy are both unset, fall back to the mod binding."""
    from services.server_logging import resolve_log_channel

    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    mod_channel = MagicMock(spec=discord.TextChannel)
    guild.get_channel = MagicMock(
        side_effect=lambda cid: mod_channel if cid == 42 else None,
    )

    def fake_get_binding(_gid, _sub, binding_name, *, expected_kind=None):
        out = MagicMock()
        if binding_name == "cleanup_channel":
            out.target_id = None
        else:  # mod_channel
            out.target_id = 42
        return out

    with (
        patch(
            "core.runtime.bindings.get_binding",
            new=AsyncMock(side_effect=fake_get_binding),
        ),
        patch(
            "core.runtime.guild_resources.resolve_settings_channel",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        result = await resolve_log_channel(guild, "cleanup")
    assert result is mod_channel


@pytest.mark.asyncio
async def test_resolve_log_channel_swallows_binding_lookup_exception():
    """A get_binding exception must NOT crash logging — fall through to legacy."""
    from services.server_logging import resolve_log_channel

    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    legacy_channel = MagicMock(spec=discord.TextChannel)

    with (
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            side_effect=RuntimeError("registry busted"),
        ),
        patch(
            "core.runtime.guild_resources.resolve_settings_channel",
            new_callable=AsyncMock,
            return_value=legacy_channel,
        ),
    ):
        result = await resolve_log_channel(guild, "mod")
    assert result is legacy_channel
