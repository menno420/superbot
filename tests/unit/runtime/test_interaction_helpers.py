"""Regression tests for core.runtime.interaction_helpers.

Covers CRIT-2 (interaction handlers without defer) from the
platform-hardening plan.  Verifies:

- safe_defer is idempotent when response.is_done()
- safe_defer swallows NotFound (token expired) returning False
- safe_followup uses followup.send when response is done
- safe_followup uses response.send_message + original_response when not done
- safe_edit uses response.edit_message when not done
- safe_edit uses followup.edit_message when deferred
- all three helpers swallow recoverable exceptions and return falsy
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from core.runtime import interaction_helpers as ih


def _make_interaction(*, responded: bool = False) -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 12345
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=responded)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock(return_value=MagicMock(spec=discord.Message))
    interaction.followup.edit_message = AsyncMock()
    interaction.original_response = AsyncMock(
        return_value=MagicMock(spec=discord.Message)
    )
    interaction.message = MagicMock()
    interaction.message.id = 99999
    return interaction


class TestClampEmbedTotalBudget:
    """Discord rejects an embed whose total text exceeds 6000 even when every
    individual component is within its own limit (the !platform Runtime panel:
    many fields each <1024 summing >6000 → 400, edit silently dropped)."""

    def test_over_budget_via_many_fields_is_clamped_under_6000(self):
        embed = discord.Embed(title="T", description="D")
        for i in range(10):  # 10 × 800 = ~8000, each field value < the 1024 cap
            embed.add_field(name=f"f{i}", value="x" * 800, inline=False)
        assert ih._embed_total_len(embed) > ih._EMBED_TOTAL_LIMIT
        ih.clamp_embed(embed)
        assert ih._embed_total_len(embed) <= ih._EMBED_TOTAL_LIMIT

    def test_over_budget_via_description_and_footer_is_clamped(self):
        embed = discord.Embed(title="T", description="x" * 8000)
        embed.set_footer(text="y" * 2000)
        ih.clamp_embed(embed)
        assert ih._embed_total_len(embed) <= ih._EMBED_TOTAL_LIMIT

    def test_wellformed_embed_passes_through_unchanged(self):
        embed = discord.Embed(title="T", description="small")
        embed.add_field(name="a", value="b")
        before = ih._embed_total_len(embed)
        ih.clamp_embed(embed)
        assert ih._embed_total_len(embed) == before


class TestSafeDefer:
    @pytest.mark.asyncio
    async def test_defers_when_not_responded(self):
        i = _make_interaction(responded=False)
        ok = await ih.safe_defer(i)
        assert ok is True
        i.response.defer.assert_awaited_once_with(ephemeral=False, thinking=False)

    @pytest.mark.asyncio
    async def test_noop_when_already_responded(self):
        i = _make_interaction(responded=True)
        ok = await ih.safe_defer(i)
        assert ok is True
        i.response.defer.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_swallows_token_expired_returns_false(self):
        i = _make_interaction(responded=False)
        i.response.defer.side_effect = discord.NotFound(MagicMock(), "expired")
        ok = await ih.safe_defer(i)
        assert ok is False

    @pytest.mark.asyncio
    async def test_passes_ephemeral_and_thinking(self):
        i = _make_interaction(responded=False)
        await ih.safe_defer(i, ephemeral=True, thinking=True)
        i.response.defer.assert_awaited_once_with(ephemeral=True, thinking=True)


class TestSafeFollowup:
    @pytest.mark.asyncio
    async def test_uses_followup_when_responded(self):
        i = _make_interaction(responded=True)
        msg = await ih.safe_followup(i, content="hi")
        assert msg is not None
        i.followup.send.assert_awaited_once()
        i.response.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_uses_send_message_when_not_responded(self):
        i = _make_interaction(responded=False)
        msg = await ih.safe_followup(i, content="hi")
        i.response.send_message.assert_awaited_once()
        i.followup.send.assert_not_awaited()
        i.original_response.assert_awaited_once()
        assert msg is not None

    @pytest.mark.asyncio
    async def test_returns_none_on_token_expired(self):
        i = _make_interaction(responded=True)
        i.followup.send.side_effect = discord.NotFound(MagicMock(), "expired")
        msg = await ih.safe_followup(i, content="hi")
        assert msg is None

    @pytest.mark.asyncio
    async def test_passes_embed_view_ephemeral(self):
        i = _make_interaction(responded=True)
        embed = MagicMock()
        view = MagicMock()
        await ih.safe_followup(i, content="x", embed=embed, view=view, ephemeral=True)
        call_kwargs = i.followup.send.call_args.kwargs
        assert call_kwargs.get("content") == "x"
        assert call_kwargs.get("embed") is embed
        assert call_kwargs.get("view") is view
        assert call_kwargs.get("ephemeral") is True


class TestSafeEdit:
    @pytest.mark.asyncio
    async def test_uses_response_edit_when_not_responded(self):
        i = _make_interaction(responded=False)
        ok = await ih.safe_edit(i, content="updated")
        assert ok is True
        i.response.edit_message.assert_awaited_once()
        i.followup.edit_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_uses_followup_edit_when_deferred(self):
        i = _make_interaction(responded=True)
        ok = await ih.safe_edit(i, content="updated")
        assert ok is True
        i.followup.edit_message.assert_awaited_once()
        i.response.edit_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_swallows_not_found_returns_false(self):
        i = _make_interaction(responded=False)
        i.response.edit_message.side_effect = discord.NotFound(MagicMock(), "gone")
        ok = await ih.safe_edit(i, content="updated")
        assert ok is False

    @pytest.mark.asyncio
    async def test_clamps_oversized_embed_before_edit(self):
        # Regression: a field value > 1024 chars made Discord reject the
        # whole edit (400 Invalid Form Body) and the panel silently
        # froze.  safe_edit must clamp before sending.
        i = _make_interaction(responded=False)
        embed = discord.Embed(title="x")
        embed.add_field(name="big", value="A" * 2000, inline=False)
        ok = await ih.safe_edit(i, embed=embed)
        assert ok is True
        sent = i.response.edit_message.await_args.kwargs["embed"]
        assert len(sent.fields[0].value) == 1024

    @pytest.mark.asyncio
    async def test_sets_attachments_in_place_when_provided(self):
        # In-place image management: a panel can carry a PIL card on its own
        # anchor message instead of a separate ephemeral that stacks.
        i = _make_interaction(responded=False)
        f = MagicMock(spec=discord.File)
        ok = await ih.safe_edit(i, content="x", attachments=[f])
        assert ok is True
        assert i.response.edit_message.await_args.kwargs["attachments"] == [f]

    @pytest.mark.asyncio
    async def test_clears_attachments_with_empty_list(self):
        # An empty list explicitly clears a prior card so it never lingers on
        # the next screen (the navigate-away edit passes attachments=[]).
        i = _make_interaction(responded=True)
        ok = await ih.safe_edit(i, content="x", attachments=[])
        assert ok is True
        assert i.followup.edit_message.await_args.kwargs["attachments"] == []

    @pytest.mark.asyncio
    async def test_omits_attachments_when_none(self):
        # Default: do not touch attachments → Discord preserves the message's
        # existing files (the historical behaviour for text-only panel edits).
        i = _make_interaction(responded=False)
        ok = await ih.safe_edit(i, content="x")
        assert ok is True
        assert "attachments" not in i.response.edit_message.await_args.kwargs


class TestClampEmbed:
    """Regression tests for clamp_embed (embed size-limit hardening)."""

    def test_wellformed_embed_passes_through_unchanged(self):
        embed = discord.Embed(title="t", description="d")
        embed.add_field(name="n", value="v", inline=False)
        ih.clamp_embed(embed)
        assert embed.title == "t"
        assert embed.description == "d"
        assert embed.fields[0].name == "n"
        assert embed.fields[0].value == "v"

    def test_field_value_truncated_to_1024(self):
        embed = discord.Embed()
        embed.add_field(name="big", value="A" * 5000, inline=False)
        ih.clamp_embed(embed)
        assert len(embed.fields[0].value) == 1024
        assert embed.fields[0].value.endswith("…")

    def test_field_inline_preserved_on_truncation(self):
        embed = discord.Embed()
        embed.add_field(name="big", value="A" * 5000, inline=True)
        ih.clamp_embed(embed)
        assert embed.fields[0].inline is True

    def test_description_truncated_to_4096(self):
        embed = discord.Embed(description="D" * 9000)
        ih.clamp_embed(embed)
        assert len(embed.description) == 4096

    def test_title_truncated_to_256(self):
        embed = discord.Embed(title="T" * 400)
        ih.clamp_embed(embed)
        assert len(embed.title) == 256

    def test_footer_truncated_to_2048(self):
        embed = discord.Embed()
        embed.set_footer(text="F" * 4000)
        ih.clamp_embed(embed)
        assert len(embed.footer.text) == 2048

    def test_excess_fields_dropped_to_25(self):
        embed = discord.Embed()
        for idx in range(30):
            embed.add_field(name=f"f{idx}", value=str(idx))
        ih.clamp_embed(embed)
        assert len(embed.fields) == 25

    def test_returns_same_embed_instance(self):
        embed = discord.Embed(title="ok")
        assert ih.clamp_embed(embed) is embed
