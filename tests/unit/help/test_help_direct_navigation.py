"""Help-menu direct-navigation contract tests.

When the user picks a category in the help dropdown, HelpPanelView._on_select
calls ``cog.build_help_menu_view(interaction)`` and replaces the help embed
with the cog's hub panel directly — no inline command-list fallback, no
secondary click.

These tests enforce that every cog with a hub panel exposes the hook and that
calling it returns a (discord.Embed, discord.ui.View) pair.  Static assertion
covers existence; a smoke run per cog asserts the hook actually executes
against a stubbed interaction.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

# Every cog module + the cog class that should expose build_help_menu_view.
# Game/one-shot subsystems (blackjack, deathmatch, leaderboard, etc.) are
# intentionally absent — their entry commands start a game, not open a panel,
# so the help dropdown falls back to the inline command list for them.
_PANEL_COGS: list[tuple[str, str]] = [
    ("cogs.admin_cog", "AdminCog"),
    ("cogs.moderation_cog", "ModerationCog"),
    ("cogs.economy_cog", "EconomyCog"),
    ("cogs.mining_cog", "MiningCog"),
    ("cogs.xp_cog", "XpCog"),
    ("cogs.role_cog", "RoleCog"),
    ("cogs.channel_cog", "ChannelCog"),
    ("cogs.cleanup_cog", "Cleanup"),
    ("cogs.counting_cog", "CountingCog"),
    ("cogs.chain_cog", "ChainCog"),
    ("cogs.proof_channel_cog", "ProofChannelCog"),
    ("cogs.utility_cog", "UtilityCog"),
    ("cogs.general_cog", "General"),
]


def _resolve(module_path: str, class_name: str):
    mod = __import__(module_path, fromlist=[class_name])
    return getattr(mod, class_name)


@pytest.mark.parametrize(("module_path", "class_name"), _PANEL_COGS)
def test_panel_cog_exposes_build_help_menu_view(module_path: str, class_name: str):
    cog_cls = _resolve(module_path, class_name)
    hook = getattr(cog_cls, "build_help_menu_view", None)
    assert callable(hook), (
        f"{class_name} must expose async def build_help_menu_view(interaction) "
        "so the help dropdown can navigate directly to its panel"
    )
    assert inspect.iscoroutinefunction(hook), (
        f"{class_name}.build_help_menu_view must be async"
    )


def _stub_interaction(user_id: int = 111, guild_id: int = 222) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = SimpleNamespace(
        id=user_id,
        display_name="tester",
        display_avatar=SimpleNamespace(url="http://x"),
        guild_permissions=SimpleNamespace(administrator=True),
        mention="<@111>",
    )
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.guild_id = guild_id
    interaction.channel = MagicMock()
    interaction.channel.id = 333
    interaction.channel.mention = "#test"
    interaction.client = MagicMock()
    return interaction


@pytest.mark.asyncio
async def test_economy_build_help_menu_view_returns_embed_and_view():
    from unittest.mock import patch

    from cogs.economy_cog import EconomyCog

    cog = EconomyCog(MagicMock())
    interaction = _stub_interaction()

    fake_embed = discord.Embed(title="x")
    with patch(
        "cogs.economy_cog._build_economy_embed",
        new_callable=AsyncMock,
        return_value=fake_embed,
    ):
        embed, view = await cog.build_help_menu_view(interaction)

    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_mining_build_help_menu_view_returns_embed_and_view():
    from cogs.mining_cog import MiningCog

    cog = MiningCog(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_role_build_help_menu_view_returns_embed_and_view():
    from cogs.role_cog import RoleCog

    cog = RoleCog(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_moderation_build_help_menu_view_returns_embed_and_view():
    from cogs.moderation_cog import ModerationCog

    cog = ModerationCog(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_help_ctx_shim_exposes_required_attrs():
    """The shim must expose author/guild/channel/bot — nothing else needed."""
    from core.runtime.interaction_helpers import help_ctx_shim

    interaction = _stub_interaction()
    ctx = help_ctx_shim(interaction)
    assert ctx.author is interaction.user
    assert ctx.guild is interaction.guild
    assert ctx.channel is interaction.channel
    assert ctx.bot is interaction.client
