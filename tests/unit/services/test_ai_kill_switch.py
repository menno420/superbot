"""M5 — kill switch test.

Flipping ``ai_guild_policy.enabled`` to False stops the next
resolve() call immediately because the generation counter changes
and the cached bundle is invalidated.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import PolicyDenialReason  # noqa: E402
from services import ai_natural_language_policy as policy  # noqa: E402
from services.ai_natural_language_policy import MessageContext  # noqa: E402
from utils.db import ai as ai_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub(monkeypatch):
    state = {
        "policy": {
            "guild_id": 1, "enabled": True, "natural_language_enabled": True,
            "default_provider": "deterministic", "default_model": "",
            "minimum_level_default": 0, "cooldown_seconds": 0,
            "fresh_user_mention_allowance": 0,
            "guild_instruction_profile_id": None, "generation": 1,
        },
    }

    async def _get_guild_policy(gid):
        return state["policy"]

    async def _list(*a, **kw):
        return []

    monkeypatch.setattr(ai_db, "get_guild_policy", _get_guild_policy)
    monkeypatch.setattr(ai_db, "list_channel_policies", _list)
    monkeypatch.setattr(ai_db, "list_category_policies", _list)
    monkeypatch.setattr(ai_db, "list_role_policies", _list)
    policy._reset_for_tests()
    yield state
    policy._reset_for_tests()


def _ctx() -> MessageContext:
    return MessageContext(
        guild_id=1, channel_id=2, category_id=None, user_id=3,
        user_level=5, user_role_ids=(), is_mention=False,
        is_fresh_user=False,
    )


async def test_kill_switch_flip_stops_next_resolve(_stub):
    first = await policy.resolve(_ctx())
    assert first.allowed is True

    # Operator flips ai.enabled=false; generation bumps so the
    # cached bundle is invalidated.
    _stub["policy"]["enabled"] = False
    _stub["policy"]["generation"] = 2

    second = await policy.resolve(_ctx())
    assert second.allowed is False
    assert second.reason_code is PolicyDenialReason.AI_GLOBALLY_DISABLED
