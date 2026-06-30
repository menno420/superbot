"""Unit tests for cogs/ai_review_cog.py.

Pins the embed/summary helpers and the correction-detection eligibility: a
correction is only logged when the target is a *known* AI answer (in the
service registry) and (for replies) the text reads as a correction.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

import discord  # noqa: E402

from cogs import ai_review_cog as cog_mod  # noqa: E402
from core.runtime.message_pipeline import MessagePipelineContext  # noqa: E402
from services import ai_review_log_service as svc  # noqa: E402


# --------------------------------------------------------------- helpers


def test_clip_truncates_and_handles_empty() -> None:
    assert cog_mod._clip(None) == ""
    assert cog_mod._clip("   ") == ""
    assert cog_mod._clip("abc") == "abc"
    out = cog_mod._clip("x" * 5000, cap=100)
    assert len(out) == 100 and out.endswith("…")


def test_build_entry_embed_unknown_vs_correction() -> None:
    unknown = cog_mod._build_entry_embed(
        {
            "kind": svc.KIND_UNKNOWN,
            "reason_code": "grounding_failed",
            "question": "how much cash",
            "answer": "blocked",
            "user_id": 42,
            "entry_id": 5,
        },
    )
    assert isinstance(unknown, discord.Embed)
    assert "couldn't answer" in (unknown.title or "").lower()

    correction = cog_mod._build_entry_embed(
        {
            "kind": svc.KIND_CORRECTION,
            "reason_code": "reply",
            "question": "q",
            "answer": "a",
            "correction": "no it's 5",
            "corrected_by": 7,
            "entry_id": 6,
        },
    )
    assert "corrected" in (correction.title or "").lower()


def test_parse_export_flags() -> None:
    # default: unreviewed, both kinds.
    assert cog_mod._parse_export_flags(()) == (None, False)
    # `all` includes resolved entries.
    assert cog_mod._parse_export_flags(("all",)) == (None, True)
    # kind filters (order-independent, with aliases).
    assert cog_mod._parse_export_flags(("unknown",)) == (svc.KIND_UNKNOWN, False)
    assert cog_mod._parse_export_flags(("c",)) == (svc.KIND_CORRECTION, False)
    assert cog_mod._parse_export_flags(("all", "correction")) == (
        svc.KIND_CORRECTION,
        True,
    )


def test_entry_summary_shapes() -> None:
    s_unknown = cog_mod._entry_summary(
        {"kind": svc.KIND_UNKNOWN, "question": "q", "answer": "a", "id": 1},
    )
    assert "Q:" in s_unknown and "A:" in s_unknown
    s_corr = cog_mod._entry_summary(
        {"kind": svc.KIND_CORRECTION, "question": "q", "correction": "fix", "id": 2},
    )
    assert "Fix:" in s_corr


# --------------------------------------------------------------- listeners


@pytest.fixture
def _capture(monkeypatch):
    calls: list[dict] = []

    async def _record_correction(**kwargs):
        calls.append(kwargs)
        return 1

    monkeypatch.setattr(svc, "record_correction", _record_correction)
    svc._reset_for_tests()
    yield calls


def _remember(reply_id: int) -> None:
    svc.remember_answer(
        reply_id,
        guild_id=1,
        channel_id=2,
        user_id=3,
        message_id=4,
        question="q",
        answer="a",
        task="t",
        route="r",
        provider="p",
        model="m",
    )


def _cog() -> cog_mod.AIReviewCog:
    return cog_mod.AIReviewCog(SimpleNamespace(user=SimpleNamespace(id=999)))


def _ctx(message: object) -> MessagePipelineContext:
    # The pipeline pre-filters bot messages + DMs, so the stage only ever sees a
    # guild-bound non-bot author — the test messages mirror that.
    return MessagePipelineContext(bot=SimpleNamespace(), message=message)  # type: ignore[arg-type]


async def test_reply_correction_for_known_answer_is_logged(_capture) -> None:
    _remember(900)
    msg = SimpleNamespace(
        author=SimpleNamespace(id=55),
        reference=SimpleNamespace(message_id=900),
        content="no, it's actually 5",
    )
    await cog_mod.AICorrectionStage().process(_ctx(msg))
    assert len(_capture) == 1
    assert _capture[0]["signal"] == svc.SIGNAL_REPLY
    assert _capture[0]["correction"] == "no, it's actually 5"
    assert _capture[0]["corrected_by"] == 55


async def test_reply_that_is_not_a_correction_is_ignored(_capture) -> None:
    _remember(901)
    msg = SimpleNamespace(
        author=SimpleNamespace(id=55),
        reference=SimpleNamespace(message_id=901),
        content="thanks, tell me more",
    )
    await cog_mod.AICorrectionStage().process(_ctx(msg))
    assert _capture == []


async def test_reply_to_unknown_message_is_ignored(_capture) -> None:
    msg = SimpleNamespace(
        author=SimpleNamespace(id=55),
        reference=SimpleNamespace(message_id=12345),  # not in the registry
        content="no that's wrong",
    )
    await cog_mod.AICorrectionStage().process(_ctx(msg))
    assert _capture == []


async def test_non_reply_message_is_ignored(_capture) -> None:
    _remember(903)
    msg = SimpleNamespace(
        author=SimpleNamespace(id=55),
        reference=None,
        content="no that's wrong",
    )
    await cog_mod.AICorrectionStage().process(_ctx(msg))
    assert _capture == []


async def test_thumbsdown_reaction_on_known_answer_is_logged(_capture) -> None:
    _remember(700)
    payload = SimpleNamespace(guild_id=1, user_id=55, message_id=700, emoji="👎")
    await _cog().on_raw_reaction_add(payload)
    assert len(_capture) == 1
    assert _capture[0]["signal"] == svc.SIGNAL_REACTION
    assert _capture[0]["corrected_by"] == 55


async def test_non_thumbsdown_reaction_is_ignored(_capture) -> None:
    _remember(701)
    payload = SimpleNamespace(guild_id=1, user_id=55, message_id=701, emoji="👍")
    await _cog().on_raw_reaction_add(payload)
    assert _capture == []
