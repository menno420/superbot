"""Tests for the Project Moon (Limbus) browse/lookup surface."""

from __future__ import annotations

import discord
import pytest

from cogs.project_moon_cog import ProjectMoonCog
from services import projmoon_data_service as data
from views.projmoon import (
    build_entry_embed,
    build_kind_embed,
    build_origins_embed,
    build_overview_embed,
)


class _FakeCtx:
    def __init__(self):
        self.author = object()
        self.sent: list[dict] = []

    async def send(self, **kwargs):
        self.sent.append(kwargs)
        return None


@pytest.fixture(autouse=True)
def _fresh_cache():
    data.reset_cache()
    yield
    data.reset_cache()


def _cog():
    return ProjectMoonCog(bot=object())


# ---- embed builders (pure) -------------------------------------------------


def test_overview_embed_lists_every_kind():
    embed = build_overview_embed()
    names = {f.name for f in embed.fields}
    for label in data.KIND_LABELS.values():
        assert any(label in n for n in names), label


def test_kind_embed_lists_all_entries():
    embed = build_kind_embed("sinner")
    assert len(embed.fields) == 12


def test_entry_embed_shows_extra_fields():
    aleph = data.resolve("ALEPH", kind="ego_grade")
    embed = build_entry_embed(aleph)
    field_names = {f.name for f in embed.fields}
    assert "Category" in field_names
    assert "Grade rank" in field_names


def test_sinner_entry_embed_shows_literary_origin():
    gregor = data.resolve("Gregor", kind="sinner")
    embed = build_entry_embed(gregor)
    origin = next(f for f in embed.fields if f.name == "Literary origin")
    assert "Metamorphosis" in origin.value
    assert "Kafka" in origin.value


def test_origins_embed_lists_all_twelve_sinners():
    embed = build_origins_embed()
    for name in ("Yi Sang", "Faust", "Outis", "Gregor"):
        assert name in embed.description
    # one line per Sinner.
    assert embed.description.count("**") == 12 * 2


# ---- command callbacks -----------------------------------------------------


@pytest.mark.asyncio
async def test_category_lookup_hit_sends_entry_embed():
    cog, ctx = _cog(), _FakeCtx()
    await cog._category_lookup(ctx, "status", "sinking")
    assert len(ctx.sent) == 1
    embed: discord.Embed = ctx.sent[0]["embed"]
    assert "Sinking" in embed.title


@pytest.mark.asyncio
async def test_category_lookup_miss_is_honest():
    cog, ctx = _cog(), _FakeCtx()
    await cog._category_lookup(ctx, "sinner", "gandalf")
    embed: discord.Embed = ctx.sent[0]["embed"]
    assert "gandalf" in embed.description.lower()


@pytest.mark.asyncio
async def test_category_lookup_empty_lists_the_category():
    cog, ctx = _cog(), _FakeCtx()
    await cog._category_lookup(ctx, "sin", "")
    embed: discord.Embed = ctx.sent[0]["embed"]
    assert len(embed.fields) == 7


@pytest.mark.asyncio
async def test_pm_lookup_resolves_across_kinds():
    cog, ctx = _cog(), _FakeCtx()
    await cog.pm_lookup.callback(cog, ctx, query="heathcliff")
    embed: discord.Embed = ctx.sent[0]["embed"]
    assert "Heathcliff" in embed.title


@pytest.mark.asyncio
async def test_pm_lookup_unknown_is_honest():
    cog, ctx = _cog(), _FakeCtx()
    await cog.pm_lookup.callback(cog, ctx, query="not a real thing")
    embed: discord.Embed = ctx.sent[0]["embed"]
    assert "don't have" in embed.description.lower()


@pytest.mark.asyncio
async def test_pm_origins_command_sends_cross_reference():
    cog, ctx = _cog(), _FakeCtx()
    await cog.pm_origins.callback(cog, ctx)
    embed: discord.Embed = ctx.sent[0]["embed"]
    assert "literary origins" in embed.title.lower()
    assert "Dostoevsky" in embed.description
