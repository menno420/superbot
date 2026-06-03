"""Tests for the deterministic BTD6 answer embed builder + renderer (PR2)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.btd6.answer_embed import BTD6RenderContext, build_answer_embed  # noqa: E402
from views.btd6.answer_renderer import render_btd6_answer  # noqa: E402


def test_embed_data_comes_from_facts_with_tag_stripped():
    ctx = BTD6RenderContext(
        facts=(
            "[btd6_tower] Dart Monkey — base cost: 200 (medium)",
            "[btd6_tower] top: Sharp Shots ($140)",
        ),
        game_version="54.0",
    )
    embed = build_answer_embed("Dart Monkey is a cheap starter.", ctx)
    assert embed is not None
    assert embed.description == "Dart Monkey is a cheap starter."
    field = embed.fields[0]
    # Provenance tag stripped; digits come from the grounded facts.
    assert "[btd6_tower]" not in field.value
    assert "base cost: 200" in field.value
    assert "$140" in field.value
    assert "54.0" in (embed.footer.text or "")


def test_embed_truncation_label_reports_total():
    facts = tuple(f"[btd6_tower] fact line {i}" for i in range(15))
    embed = build_answer_embed("prose", BTD6RenderContext(facts=facts, game_version="54.0"))
    assert embed is not None
    assert "showing 10 of 15" in embed.fields[0].name


def test_embed_none_when_no_anchorable_facts():
    assert build_answer_embed("hi", BTD6RenderContext(facts=(), game_version="54.0")) is None
    # Facts that clean down to nothing also fall through to plain text.
    assert (
        build_answer_embed("hi", BTD6RenderContext(facts=("[btd6_x] ",), game_version="54.0"))
        is None
    )


@pytest.mark.asyncio
async def test_renderer_returns_none_without_btd6_render_context():
    resp = SimpleNamespace(text="hi")
    assert await render_btd6_answer(None, resp, None, None) is None
    assert await render_btd6_answer(None, resp, None, object()) is None


@pytest.mark.asyncio
async def test_renderer_builds_embed_and_redacts_text():
    # A raw snowflake in the model text is scrubbed by the renderer's redaction.
    resp = SimpleNamespace(text="See <@123456789012345678> — Dart Monkey costs 200.")
    ctx = BTD6RenderContext(
        facts=("[btd6_tower] Dart Monkey base cost 200",), game_version="54.0"
    )
    rendered = await render_btd6_answer(None, resp, None, ctx)
    assert rendered is not None
    assert rendered.content is None
    assert rendered.embed is not None
    assert "123456789012345678" not in (rendered.embed.description or "")


@pytest.mark.asyncio
async def test_renderer_falls_through_when_no_facts():
    resp = SimpleNamespace(text="just chatting about bloons")
    ctx = BTD6RenderContext(facts=(), game_version="54.0")
    assert await render_btd6_answer(None, resp, None, ctx) is None
