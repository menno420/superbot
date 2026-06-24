"""Embed builders for the per-round economy commands (income / rbe / round).

These render the verified per-round data (``btd6_data_service.round_cash`` /
``round_rbe`` / ``round_composition``) into the ``/btd6ref`` embeds. The numbers
themselves are pinned by the service-layer tests; here we assert the embeds
*surface* them correctly and fail visibly (red embed) on a bad range.
"""

from __future__ import annotations

import discord
import pytest

from cogs.btd6 import _builders


@pytest.mark.asyncio
async def test_income_range_shows_verified_total_and_table() -> None:
    embed = await _builders.build_income_embed(100, 120)
    assert embed.color == discord.Color.green()
    assert "rounds 100–120" in embed.title
    # Our audited total — not CyberQuincy's inflated $139,067.
    assert "$89,878" in embed.description
    assert "```" in embed.description  # the monospace table
    assert "r100" in embed.description and "r120" in embed.description
    assert "income towers" in embed.footer.text  # assumptions surfaced verbatim


@pytest.mark.asyncio
async def test_income_single_round() -> None:
    embed = await _builders.build_income_embed(100)
    assert "round 100" in embed.title
    assert "$1,534.6" in embed.description
    assert "180,374" in embed.description  # cumulative


@pytest.mark.asyncio
async def test_income_bad_range_is_red_and_explains() -> None:
    embed = await _builders.build_income_embed(200, 250)
    assert embed.color == discord.Color.red()
    assert "1-140" in embed.description


@pytest.mark.asyncio
async def test_income_full_range_elides_with_marker() -> None:
    embed = await _builders.build_income_embed(1, 140)
    assert "⋮" in embed.description  # head+tail elision marker
    assert "truncated" in embed.footer.text


@pytest.mark.asyncio
async def test_rbe_scaled_range_shows_both_columns_and_note() -> None:
    embed = await _builders.build_rbe_embed(99, 103)
    assert embed.color == discord.Color.blue()
    assert "base RBE" in embed.description and "effective" in embed.description
    assert "67,200" in embed.description  # the r100 anchor, effective column
    assert "verified BAD r100 = 67,200" in embed.footer.text


@pytest.mark.asyncio
async def test_rbe_unscaled_range_is_single_column_no_footer() -> None:
    embed = await _builders.build_rbe_embed(5, 8)
    # No "effective" column header when nothing in range scales.
    assert "effective" not in embed.description
    assert embed.footer.text is None


@pytest.mark.asyncio
async def test_rbe_single_round_shows_effective_over_base() -> None:
    embed = await _builders.build_rbe_embed(100)
    assert "67,200" in embed.description
    assert "55,760" in embed.description


@pytest.mark.asyncio
async def test_round_embed_adds_composition_and_effective_rbe() -> None:
    embed = await _builders.build_round_embed(100)
    names = {f.name for f in embed.fields}
    assert any("Bloons this round" in n for n in names)
    assert any("Effective RBE" in n for n in names)
    comp = next(f for f in embed.fields if "Bloons this round" in f.name)
    assert "BAD" in comp.value


@pytest.mark.asyncio
async def test_round_embed_below_freeplay_has_no_effective_rbe_field() -> None:
    embed = await _builders.build_round_embed(6)
    names = {f.name for f in embed.fields}
    # Composition is always shown; the effective-RBE field only when it scales.
    assert any("Bloons this round" in n for n in names)
    assert not any("Effective RBE" in n for n in names)
