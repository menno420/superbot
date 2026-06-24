"""Unit tests for the ``!xpmenu`` hub panel (`_XpHubView`).

Pins the visual card-engine **H3** migration of the XP hub: the direct
``!xpmenu`` surface now renders the same rank **image card** the ``!rank``
view does, via :func:`services.xp_helpers.build_rank_response`, while the
``build_help_menu_view`` help-nav hook stays embed-only (that seam carries no
attachment across the codebase).

These tests stub ``build_rank_response`` at the module seam — they verify the
hub's *wiring* (does it ask for the card, attach it, decorate the embed, swap
the attachment on a stat switch, and degrade cleanly without Pillow), not the
rank data itself (covered by ``test_xp_helpers_rank``).
"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.xp.main_panel import _XpHubView


def _ctx(*, admin: bool = False) -> MagicMock:
    ctx = MagicMock()
    author = MagicMock(spec=discord.Member)
    author.id = 7
    author.display_name = "AstroFox"
    author.guild_permissions = MagicMock(administrator=admin)
    ctx.author = author
    ctx.guild = MagicMock(spec=discord.Guild)
    ctx.guild.id = 42
    return ctx


def _fake_card() -> discord.File:
    return discord.File(io.BytesIO(b"\x89PNG\r\n\x1a\nfake"), filename="rank.png")


def _patch_response(card: discord.File | None):
    """Patch the hub's ``build_rank_response`` seam to return a (fresh embed, card).

    A fresh embed per call so two views decorated in one test don't share (and
    overwrite) each other's footer.
    """

    async def _resp(_member, _guild, _stat):
        return discord.Embed(description="rank"), card

    return patch(
        "views.xp.main_panel.build_rank_response", new=AsyncMock(side_effect=_resp)
    )


@pytest.mark.asyncio
async def test_build_response_attaches_card_and_decorates_embed():
    view = _XpHubView(_ctx())
    with _patch_response(_fake_card()) as resp:
        embed, card = await view.build_response()

    resp.assert_awaited_once()
    assert resp.await_args.args[2] == "both"  # default stat
    assert isinstance(card, discord.File)
    # The hub chrome is applied on top of the rank embed.
    assert embed.title == "🏆 XP Panel — AstroFox"
    assert "switch stat view" in (embed.footer.text or "").lower()


@pytest.mark.asyncio
async def test_build_response_falls_back_to_embed_only_without_pillow():
    view = _XpHubView(_ctx())
    with _patch_response(None):
        embed, card = await view.build_response()

    assert card is None  # Pillow-less host → embed-only, no attachment
    assert embed.title == "🏆 XP Panel — AstroFox"


@pytest.mark.asyncio
async def test_admin_footer_only_for_admins():
    admin_view = _XpHubView(_ctx(admin=True))
    plain_view = _XpHubView(_ctx(admin=False))
    with _patch_response(None):
        admin_embed, _ = await admin_view.build_response()
        plain_embed, _ = await plain_view.build_response()

    assert "Admin controls" in admin_embed.footer.text
    assert "Admin controls" not in plain_embed.footer.text


@pytest.mark.asyncio
async def test_stat_switch_swaps_the_card_attachment():
    view = _XpHubView(_ctx())
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    with _patch_response(_fake_card()) as resp:
        await view.btn_coins.callback(interaction)

    # Re-rendered for the chosen stat, with the new card passed as attachments.
    assert resp.await_args.args[2] == "coins"
    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert kwargs["view"] is view
    assert len(kwargs["attachments"]) == 1
    assert isinstance(kwargs["attachments"][0], discord.File)


@pytest.mark.asyncio
async def test_stat_switch_clears_attachment_on_embed_only_fallback():
    view = _XpHubView(_ctx())
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    with _patch_response(None):
        await view.btn_xp.callback(interaction)

    kwargs = interaction.response.edit_message.await_args.kwargs
    # No card → attachments explicitly cleared so the old image is removed.
    assert kwargs["attachments"] == []


@pytest.mark.asyncio
async def test_build_embed_stays_embed_only():
    # ``build_embed`` is the config-panel back-navigation path (XpConfigView →
    # parent.build_embed()); it must not touch the image-card seam — that path
    # rebuilds the parent hub embed only. (The help-nav hook and the direct
    # ``!xpmenu`` surface render the card via ``build_response``.)
    view = _XpHubView(_ctx())
    embed_stub = discord.Embed(description="rank")
    with (
        patch(
            "views.xp.main_panel._build_rank_embed",
            new=AsyncMock(return_value=embed_stub),
        ),
        patch(
            "views.xp.main_panel.build_rank_response",
            new=AsyncMock(side_effect=AssertionError("must not render a card")),
        ),
    ):
        embed = await view.build_embed()

    assert embed.title == "🏆 XP Panel — AstroFox"


@pytest.mark.asyncio
async def test_build_help_menu_view_stashes_the_card_for_the_nav_seam():
    # The cog's help-nav hook renders the same image card the direct ``!xpmenu``
    # surface does and stashes it on the view as ``help_nav_card`` so every
    # help-nav render site forwards it (visual card engine H3).
    from cogs.xp_cog import XpCog
    from views.navigation import help_nav_card

    cog = XpCog(bot=MagicMock())
    interaction = MagicMock()
    with (
        patch("cogs.xp_cog.help_ctx_shim", return_value=_ctx()),
        _patch_response(_fake_card()),
    ):
        embed, view = await cog.build_help_menu_view(interaction)

    assert embed.title == "🏆 XP Panel — AstroFox"
    assert isinstance(view.help_nav_card, discord.File)
    # The accessor the render sites use sees exactly that card.
    assert help_nav_card(view) is view.help_nav_card


@pytest.mark.asyncio
async def test_build_help_menu_view_no_card_without_pillow():
    # Pillow-less host → no card → the nav seam yields ``None`` → embed-only,
    # byte-identical to the prior help-nav behaviour.
    from cogs.xp_cog import XpCog
    from views.navigation import help_nav_card

    cog = XpCog(bot=MagicMock())
    interaction = MagicMock()
    with (
        patch("cogs.xp_cog.help_ctx_shim", return_value=_ctx()),
        _patch_response(None),
    ):
        embed, view = await cog.build_help_menu_view(interaction)

    assert embed.title == "🏆 XP Panel — AstroFox"
    assert view.help_nav_card is None
    assert help_nav_card(view) is None
