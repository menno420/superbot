"""Unit tests for ``services.btd6_ai_knowledge_block_service``.

Covers the BTD6-anchor heuristic, block composition (live state +
source status), bounded rendering, public-safety pins for the
source-status block, and defensive failure handling.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import pytest

from services import btd6_ai_context_service
from services import btd6_ai_knowledge_block_service as svc
from services.btd6_ai_context_service import (
    ActiveEventSummary,
    RestrictionSummary,
    SourceStatusSummary,
)

# ---------------------------------------------------------------------------
# Heuristics — true positives
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "what boss event is on right now?",
        "any active bloons events?",
        "what's on in BTD6 right now?",
        "is the dreadbloon boss active?",
        "what monkeys are banned in the current race?",
        "is the contested territory event running?",
        "any current odyssey?",
    ],
)
def test_state_heuristic_true_positives(text):
    assert svc.looks_like_btd6_state_question(text), text


@pytest.mark.parametrize(
    "text",
    [
        "is the btd6 data fresh?",
        "when did you last fetch ninja kiwi data?",
        "are bloons facts outdated?",
        "how old is the boss data?",
        "is the race data stale?",
    ],
)
def test_freshness_heuristic_true_positives(text):
    assert svc.looks_like_btd6_freshness_question(text), text


# ---------------------------------------------------------------------------
# Heuristics — false positives MUST stay False
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "what event is on the server right now?",
        "is the bot active?",
        "show the leaderboard for XP",
        "is the database stale?",
        "any current events in the discord?",
        "what's the active warn count?",
        "is anyone active right now?",
        "what restrictions does this role have?",
    ],
)
def test_state_heuristic_false_positives(text):
    assert not svc.looks_like_btd6_state_question(text), text


@pytest.mark.parametrize(
    "text",
    [
        "is the database stale?",
        "when did you last fetch the cache?",
        "is anyone updated on the new policy?",
        "is the data fresh in the help channel?",
    ],
)
def test_freshness_heuristic_false_positives(text):
    assert not svc.looks_like_btd6_freshness_question(text), text


# ---------------------------------------------------------------------------
# gather_btd6_bot_knowledge_blocks — happy paths
# ---------------------------------------------------------------------------


def _event(name: str = "Dreadbloon") -> ActiveEventSummary:
    return ActiveEventSummary(
        entity_kind="btd6_boss",
        entity_key="boss_xyz",
        name=name,
        start_ms=None,
        end_ms=None,
        fetched_at=datetime.now(tz=timezone.utc),
        freshness="fresh",
        source_name="data.ninjakiwi.com",
    )


def _restriction(entity_id: str = "quincy", is_hero: bool = True) -> RestrictionSummary:
    return RestrictionSummary(
        entity_id=entity_id,
        is_hero=is_hero,
        event_kind="btd6_race",
        event_name="Reversed Loop",
        stance="banned",
        max_count=0,
        fetched_at=datetime.now(tz=timezone.utc),
        source_name="data.ninjakiwi.com",
        sentinel_all_heroes_banned=False,
    )


def _status(key: str = "nk_btd6_races", bucket: str = "fresh") -> SourceStatusSummary:
    return SourceStatusSummary(
        source_key=key,
        source_name=key.replace("nk_btd6_", "").title(),
        trust_tier=1,
        enabled=True,
        last_fetched_at=datetime.now(tz=timezone.utc),
        fact_count=12,
        freshness=bucket,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_gather_emits_live_state_block_when_state_question(monkeypatch):
    async def _events():
        return (_event(),)

    async def _restrictions(scope="all"):
        return (_restriction(),)

    monkeypatch.setattr(btd6_ai_context_service, "get_current_events", _events)
    monkeypatch.setattr(
        btd6_ai_context_service, "get_active_restrictions", _restrictions
    )

    out = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="what boss event is on right now?",
    )
    assert len(out) == 1
    assert out[0].kind == "bot_btd6_live_state"
    assert "Currently active in BTD6" in out[0].text
    assert "Dreadbloon" in out[0].text
    assert "quincy" in out[0].text


@pytest.mark.asyncio
async def test_gather_emits_source_status_block_when_freshness_question(monkeypatch):
    async def _status_stub(*, public_safe=True):
        return (_status("nk_btd6_races"), _status("nk_btd6_bosses", bucket="aging"))

    monkeypatch.setattr(btd6_ai_context_service, "get_source_status", _status_stub)

    out = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="is the btd6 data fresh?",
    )
    assert len(out) == 1
    assert out[0].kind == "bot_btd6_source_status"
    assert "BTD6 data sources" in out[0].text


@pytest.mark.asyncio
async def test_gather_returns_both_blocks_when_both_questions(monkeypatch):
    async def _events():
        return (_event(),)

    async def _restrictions(scope="all"):
        return (_restriction(),)

    async def _status_stub(*, public_safe=True):
        return (_status(),)

    monkeypatch.setattr(btd6_ai_context_service, "get_current_events", _events)
    monkeypatch.setattr(
        btd6_ai_context_service, "get_active_restrictions", _restrictions
    )
    monkeypatch.setattr(btd6_ai_context_service, "get_source_status", _status_stub)

    out = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="what boss is on and is the btd6 data fresh?",
    )
    kinds = {b.kind for b in out}
    assert kinds == {"bot_btd6_live_state", "bot_btd6_source_status"}


# ---------------------------------------------------------------------------
# Empty / failure modes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_live_state_block_when_events_and_restrictions_empty(monkeypatch):
    async def _empty():
        return ()

    async def _empty_scoped(scope="all"):
        return ()

    monkeypatch.setattr(btd6_ai_context_service, "get_current_events", _empty)
    monkeypatch.setattr(
        btd6_ai_context_service, "get_active_restrictions", _empty_scoped
    )
    out = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="what boss event is on right now?",
    )
    assert out == ()


@pytest.mark.asyncio
async def test_no_source_status_block_when_facade_empty(monkeypatch):
    async def _empty(*, public_safe=True):
        return ()

    monkeypatch.setattr(btd6_ai_context_service, "get_source_status", _empty)
    out = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="is the btd6 data fresh?",
    )
    assert out == ()


@pytest.mark.asyncio
async def test_live_state_block_logs_and_returns_none_on_failure(monkeypatch, caplog):
    async def _boom():
        raise RuntimeError("nope")

    monkeypatch.setattr(btd6_ai_context_service, "get_current_events", _boom)
    with caplog.at_level(logging.ERROR, logger="bot.services.btd6_ai_knowledge_block"):
        out = await svc.gather_btd6_bot_knowledge_blocks(
            user_text="what boss is on right now?",
        )
    assert out == ()
    assert any("_live_state_block failed" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Bounded rendering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_live_state_block_caps_lines(monkeypatch):
    async def _many_events():
        return tuple(_event(name=f"Event{i}") for i in range(50))

    async def _no_restrictions(scope="all"):
        return ()

    monkeypatch.setattr(btd6_ai_context_service, "get_current_events", _many_events)
    monkeypatch.setattr(
        btd6_ai_context_service, "get_active_restrictions", _no_restrictions
    )
    out = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="what BTD6 events are active right now?",
    )
    assert len(out) == 1
    line_count = out[0].text.count("\n") + 1
    # 1 header + ≤24 entries == ≤25 total lines.
    assert line_count <= svc._LIVE_STATE_MAX_LINES
    assert len(out[0].text) <= svc._LIVE_STATE_MAX_CHARS


@pytest.mark.asyncio
async def test_source_status_block_caps_lines(monkeypatch):
    async def _many(*, public_safe=True):
        return tuple(_status(key=f"src_{i}") for i in range(40))

    monkeypatch.setattr(btd6_ai_context_service, "get_source_status", _many)
    out = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="is the btd6 data fresh?",
    )
    assert len(out) == 1
    line_count = out[0].text.count("\n") + 1
    assert line_count <= svc._SOURCE_STATUS_MAX_LINES
    assert len(out[0].text) <= svc._SOURCE_STATUS_MAX_CHARS


# ---------------------------------------------------------------------------
# Public-safety pin — source status MUST NOT leak URLs / hashes / actors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_source_status_block_never_leaks_internals(monkeypatch):
    async def _stub(*, public_safe=True):
        return (
            _status(key="nk_btd6_races"),
            _status(key="nk_btd6_bosses", bucket="never"),
        )

    monkeypatch.setattr(btd6_ai_context_service, "get_source_status", _stub)
    out = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="is the btd6 data fresh?",
    )
    assert out
    rendered = out[0].text
    assert not re.search(r"https?://", rendered)
    assert "_hash" not in rendered
    assert not re.search(r"_by\b", rendered)
    assert "path_template" not in rendered
    assert "path_params" not in rendered


# ---------------------------------------------------------------------------
# Crosspath validity rules (live miss, 2026-06-10)
# ---------------------------------------------------------------------------


def test_answer_guidance_block_carries_crosspath_validity_rules():
    """The guidance block fired on "five 0-2-4 dart monkeys" yet the model
    still claimed a tower "can only upgrade ONE path" and called 0-2-4
    invalid — the block taught notation but not validity. Pin the rules."""
    text = svc._btd6_answer_guidance_block().text
    assert "up to TWO" in text
    assert "only ONE path may go above tier 2" in text
    assert "0-2-4" in text
    assert "2-2-2" in text  # named as invalid
    assert "base cost plus every purchased upgrade" in text


@pytest.mark.asyncio
async def test_guidance_block_fires_for_dash_crosspath_question():
    blocks = await svc.gather_btd6_bot_knowledge_blocks(
        user_text="five 0-2-4 dart monkeys by round 60 at medium",
    )
    assert any(b.kind == "bot_btd6_answer_guidance" for b in blocks)
