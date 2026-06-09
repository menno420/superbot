"""Resolver precedence tests for ``ai_orchestration_policy`` (Phase 3).

Stubs the ``utils.db.ai`` read primitives so the resolver exercises the
channel > category > guild > default precedence without a real database.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import ToolRequirementMode  # noqa: E402
from services import ai_orchestration_policy as orch  # noqa: E402
from services import ai_orchestration_presets as presets  # noqa: E402
from utils.db import ai as ai_db  # noqa: E402

_CTX = orch.OrchestrationContext(guild_id=1, channel_id=3, category_id=9)


@pytest.fixture(autouse=True)
def _stub_ai_db(monkeypatch):
    state: dict[str, Any] = {"policy": None, "channel": {}, "category": {}}

    async def _get_guild_policy(guild_id: int):
        return state["policy"]

    async def _list_channel_policies(guild_id: int):
        return [dict(row, channel_id=cid) for cid, row in state["channel"].items()]

    async def _list_category_policies(guild_id: int):
        return [dict(row, category_id=cid) for cid, row in state["category"].items()]

    monkeypatch.setattr(ai_db, "get_guild_policy", _get_guild_policy)
    monkeypatch.setattr(ai_db, "list_channel_policies", _list_channel_policies)
    monkeypatch.setattr(ai_db, "list_category_policies", _list_category_policies)
    orch._reset_for_tests()
    return state


async def test_default_when_nothing_set(_stub_ai_db) -> None:
    d = await orch.resolve(_CTX)
    assert d.profile_key == presets.DEFAULT_PROFILE_KEY
    assert d.source == "default"
    # Byte-identical default: no narrowing, AUTO, hop-bounded budget only.
    assert d.enabled_toolsets is None
    assert d.disabled_tools == ()
    assert d.tool_choice.mode is ToolRequirementMode.AUTO
    assert d.tool_budget.max_calls is None


async def test_guild_profile_used(_stub_ai_db) -> None:
    _stub_ai_db["policy"] = {
        "generation": 1,
        "orchestration_profile": "balanced_helper",
    }
    d = await orch.resolve(_CTX)
    assert d.profile_key == "balanced_helper"
    assert d.source == "guild"


async def test_category_overrides_guild(_stub_ai_db) -> None:
    _stub_ai_db["policy"] = {
        "generation": 1,
        "orchestration_profile": "balanced_helper",
    }
    _stub_ai_db["category"] = {9: {"orchestration_profile": "btd6_grounded"}}
    d = await orch.resolve(_CTX)
    assert d.profile_key == "btd6_grounded"
    assert d.source == "category"
    assert d.enabled_toolsets is not None  # narrowed


async def test_channel_overrides_category(_stub_ai_db) -> None:
    _stub_ai_db["policy"] = {
        "generation": 1,
        "orchestration_profile": "balanced_helper",
    }
    _stub_ai_db["category"] = {9: {"orchestration_profile": "btd6_grounded"}}
    _stub_ai_db["channel"] = {3: {"orchestration_profile": "no_tools"}}
    d = await orch.resolve(_CTX)
    assert d.profile_key == "no_tools"
    assert d.source == "channel"
    assert d.enabled_toolsets == ()
    assert d.tool_choice.mode is ToolRequirementMode.NONE


async def test_null_channel_falls_through(_stub_ai_db) -> None:
    _stub_ai_db["category"] = {9: {"orchestration_profile": "btd6_grounded"}}
    _stub_ai_db["channel"] = {3: {"orchestration_profile": None}}  # explicit NULL
    d = await orch.resolve(_CTX)
    assert d.source == "category"


async def test_unknown_stored_key_degrades_to_default(_stub_ai_db) -> None:
    _stub_ai_db["policy"] = {"generation": 1, "orchestration_profile": "removed_preset"}
    d = await orch.resolve(_CTX, dry_run=True)
    assert d.profile_key == presets.DEFAULT_PROFILE_KEY
    assert d.source == "default"
    assert any("unknown_profile" in step for step in d.source_trace)


async def test_dry_run_trace_only_when_requested(_stub_ai_db) -> None:
    _stub_ai_db["policy"] = {"generation": 1, "orchestration_profile": "btd6_grounded"}
    live = await orch.resolve(_CTX)
    assert live.source_trace == ()
    dry = await orch.resolve(_CTX, dry_run=True)
    assert dry.source_trace  # populated
    assert any("resolved:" in step for step in dry.source_trace)


async def test_db_fault_degrades_to_default(monkeypatch) -> None:
    async def _boom(guild_id: int):
        raise RuntimeError("db down")

    monkeypatch.setattr(ai_db, "get_guild_policy", _boom)
    orch._reset_for_tests()
    d = await orch.resolve(_CTX)
    assert d.profile_key == presets.DEFAULT_PROFILE_KEY
    assert d.source == "default"


async def test_invalidate_clears_cache(_stub_ai_db) -> None:
    _stub_ai_db["policy"] = {
        "generation": 1,
        "orchestration_profile": "balanced_helper",
    }
    first = await orch.resolve(_CTX)
    assert first.profile_key == "balanced_helper"
    # Same generation → cached; a profile change without a generation bump is
    # invisible until invalidate (mirrors the mutation seam's invalidate call).
    _stub_ai_db["policy"]["orchestration_profile"] = "no_tools"
    cached = await orch.resolve(_CTX)
    assert cached.profile_key == "balanced_helper"  # still cached
    orch.invalidate(1)
    fresh = await orch.resolve(_CTX)
    assert fresh.profile_key == "no_tools"
