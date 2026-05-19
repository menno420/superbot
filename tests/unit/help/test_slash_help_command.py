"""PR #9 — tests for the ``/help`` slash front door.

The slash command resolves identically to ``!help`` because both
share the ``HelpRoute`` resolver in ``cogs.help.route``. These
tests pin the parity contract:

* ``/help`` (no argument) opens the same Help Home view as the
  prefix path, via ``resolve_help_panel_state``.
* ``/help <name>`` resolves through ``_resolve_route`` + ``_open_route``
  identically to ``!help <name>``.
* The Back-to-Help button is attached to hub/subsystem routes so
  the user can return to the category index.
* Unknown names produce an ephemeral "not found" reply.
* Every slash response is ephemeral (slash help is personal).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs import help_cog


def _mock_interaction(*, user_id: int = 1, guild_id: int = 42) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.id = user_id
    interaction.user.roles = []
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.guild_id = guild_id
    interaction.channel = MagicMock()
    interaction.channel.id = 999
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _patch_governance(member_tier: str = "user", visible: set | None = None):
    vis_result = MagicMock()
    vis_result.visible_subsystems = visible or {"games", "economy"}
    vis_result.member_tier = member_tier
    return patch.object(
        help_cog.governance_service,
        "resolve_visibility",
        new=AsyncMock(return_value=vis_result),
    )


# ---------------------------------------------------------------------------
# Slash command registration
# ---------------------------------------------------------------------------


def test_help_cog_registers_slash_command():
    """``HelpCog.help_slash`` must be decorated as an
    ``app_commands.command`` so the bot's tree picks it up on cog load.
    """
    cog = help_cog.HelpCog(bot=MagicMock())
    cmd = cog.help_slash
    # discord.py wraps the bound method in a ``Command`` descriptor when
    # the cog is added to the bot; the underlying ``__discord_app_commands__``
    # marker remains accessible on the function attribute.
    assert hasattr(cog.__class__.help_slash, "_callback") or hasattr(
        cog.__class__.help_slash,
        "callback",
    ), (
        "HelpCog.help_slash must be an app_commands.command descriptor "
        "so the bot tree registers it on load."
    )
    # The command name must be exactly ``help`` so users invoke ``/help``.
    name = getattr(cog.__class__.help_slash, "name", None)
    assert name == "help"


# ---------------------------------------------------------------------------
# Default (no argument) — opens Help Home ephemerally
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_help_no_args_opens_help_home_ephemerally():
    cog = help_cog.HelpCog(bot=MagicMock())
    interaction = _mock_interaction()

    fake_embed = discord.Embed(title="Help Menu")
    fake_view = MagicMock(spec=discord.ui.View)

    with _patch_governance(), patch.object(
        help_cog,
        "resolve_help_panel_state",
        new=AsyncMock(return_value=(fake_embed, fake_view)),
    ):
        await cog.help_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs["embed"] is fake_embed
    assert kwargs["view"] is fake_view
    assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# Named-route parity: /help <name> resolves like !help <name>
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_help_named_route_resolves_via_shared_resolver():
    """``/help games`` must call ``_resolve_route`` + ``_open_route`` the
    same way ``!help games`` does. Pins the parity contract.
    """
    cog = help_cog.HelpCog(bot=MagicMock())
    interaction = _mock_interaction()

    fake_route = help_cog.HelpRoute(key="games", kind="hub", target="games")
    fake_embed = discord.Embed(title="Games Hub")
    fake_view = discord.ui.View()

    with _patch_governance(), patch.object(
        help_cog,
        "_resolve_route",
        return_value=fake_route,
    ) as resolve_mock, patch.object(
        help_cog,
        "_open_route",
        new=AsyncMock(return_value=(fake_embed, fake_view)),
    ) as open_mock, patch.object(
        help_cog,
        "_attach_back_to_help_button",
    ) as back_mock:
        await cog.help_slash.callback(cog, interaction, name="games")

    # Resolver receives the user-supplied name + the bot client.
    resolve_mock.assert_called_once_with("games", bot=cog.bot)
    # Opener receives the resolved route + governance result.
    open_mock.assert_awaited_once()
    open_kwargs = open_mock.await_args.kwargs
    assert open_kwargs["visible_subsystems"] == {"games", "economy"}
    assert open_kwargs["member_tier"] == "user"
    # Back-to-Help is attached to the sub-view before send.
    back_mock.assert_called_once_with(fake_view)
    # Response is ephemeral + carries the route's embed/view.
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs["embed"] is fake_embed
    assert kwargs["view"] is fake_view
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_slash_help_unknown_name_returns_ephemeral_not_found():
    cog = help_cog.HelpCog(bot=MagicMock())
    interaction = _mock_interaction()
    unknown_route = help_cog.HelpRoute(key="bogus", kind="unknown", target=None)

    with _patch_governance(), patch.object(
        help_cog,
        "_resolve_route",
        return_value=unknown_route,
    ), patch.object(
        help_cog,
        "_open_route",
        new=AsyncMock(),
    ) as open_mock:
        await cog.help_slash.callback(cog, interaction, name="bogus")

    open_mock.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    sent = interaction.response.send_message.await_args
    assert sent.kwargs.get("ephemeral") is True
    # The user-visible text mentions the offending input.
    content = sent.args[0] if sent.args else sent.kwargs.get("content", "")
    assert "bogus" in content


# ---------------------------------------------------------------------------
# Embed-only route (single command, advanced fallback) — no view → no back
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_help_embed_only_route_skips_back_attachment():
    """When ``_open_route`` returns ``view=None`` (e.g. single-command
    detail) the slash path sends just the embed and does NOT call
    ``_attach_back_to_help_button``.
    """
    cog = help_cog.HelpCog(bot=MagicMock())
    interaction = _mock_interaction()

    cmd_route = help_cog.HelpRoute(key="bal", kind="command", target="bal")
    fake_embed = discord.Embed(title="!bal")

    with _patch_governance(), patch.object(
        help_cog,
        "_resolve_route",
        return_value=cmd_route,
    ), patch.object(
        help_cog,
        "_open_route",
        new=AsyncMock(return_value=(fake_embed, None)),
    ), patch.object(
        help_cog,
        "_attach_back_to_help_button",
    ) as back_mock:
        await cog.help_slash.callback(cog, interaction, name="bal")

    back_mock.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs["embed"] is fake_embed
    assert "view" not in kwargs
    assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# Parity sanity: shared resolver call signature matches !help
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_and_prefix_call_resolve_route_with_same_args():
    """``/help games`` and ``!help games`` must both call
    ``_resolve_route("games", bot=...)`` so a future divergence (e.g.
    one path adding flags the other doesn't) breaks the test.
    """
    cog = help_cog.HelpCog(bot=MagicMock())

    # Slash side.
    slash_interaction = _mock_interaction()
    fake_route = help_cog.HelpRoute(key="games", kind="hub", target="games")
    with _patch_governance(), patch.object(
        help_cog,
        "_resolve_route",
        return_value=fake_route,
    ) as slash_resolve, patch.object(
        help_cog,
        "_open_route",
        new=AsyncMock(return_value=(discord.Embed(), discord.ui.View())),
    ), patch.object(
        help_cog,
        "_attach_back_to_help_button",
    ):
        await cog.help_slash.callback(cog, slash_interaction, name="games")

    # Prefix side.
    prefix_ctx = MagicMock()
    prefix_ctx.author = MagicMock(spec=discord.Member)
    prefix_ctx.author.id = 1
    prefix_ctx.author.roles = []
    prefix_ctx.guild = MagicMock()
    prefix_ctx.guild.id = 42
    prefix_ctx.channel = MagicMock()
    prefix_ctx.channel.id = 999
    prefix_ctx.bot = MagicMock()
    prefix_ctx.send = AsyncMock()
    prefix_ctx.prefix = "!"

    with _patch_governance(), patch.object(
        help_cog,
        "_resolve_route",
        return_value=fake_route,
    ) as prefix_resolve, patch.object(
        help_cog,
        "_open_route",
        new=AsyncMock(return_value=(discord.Embed(), discord.ui.View())),
    ), patch.object(
        help_cog,
        "_attach_back_to_help_button",
    ):
        await cog.help_command.callback(cog, prefix_ctx, category="games")

    # Both paths called the resolver with positional name + bot kwarg.
    assert slash_resolve.call_args.args == ("games",)
    assert prefix_resolve.call_args.args == ("games",)
    assert "bot" in slash_resolve.call_args.kwargs
    assert "bot" in prefix_resolve.call_args.kwargs
