"""Audited orchestration-mutation seam tests (Phase 3).

Stubs the DB writers / generation bump / cache invalidation / bus emit so the
authority gate + key validation + write plumbing are exercised without a real
database or event bus.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import ai_orchestration_mutation as mut  # noqa: E402
from services import ai_orchestration_policy as orch  # noqa: E402
from utils.db import ai as ai_db  # noqa: E402

_ADMIN = SimpleNamespace(
    id=42,
    guild_permissions=SimpleNamespace(administrator=True),
)
_NON_ADMIN = SimpleNamespace(
    id=7,
    guild_permissions=SimpleNamespace(administrator=False),
)


@pytest.fixture(autouse=True)
def _stub(monkeypatch):
    calls: dict[str, Any] = {"writes": [], "invalidated": [], "emitted": []}

    async def _set_guild(guild_id, *, orchestration_profile, updated_by):
        calls["writes"].append(("guild", guild_id, orchestration_profile, updated_by))
        return 5

    async def _set_channel(guild_id, channel_id, *, orchestration_profile, updated_by):
        calls["writes"].append(
            ("channel", guild_id, channel_id, orchestration_profile, updated_by),
        )

    async def _set_category(
        guild_id, category_id, *, orchestration_profile, updated_by
    ):
        calls["writes"].append(
            ("category", guild_id, category_id, orchestration_profile, updated_by),
        )

    async def _bump(guild_id):
        return 11

    def _invalidate(guild_id):
        calls["invalidated"].append(guild_id)

    async def _emit(event, guild_id, mutation_id):
        calls["emitted"].append(event)
        return True

    monkeypatch.setattr(ai_db, "set_guild_orchestration_profile", _set_guild)
    monkeypatch.setattr(ai_db, "set_channel_orchestration_profile", _set_channel)
    monkeypatch.setattr(ai_db, "set_category_orchestration_profile", _set_category)
    monkeypatch.setattr(ai_db, "bump_generation", _bump)
    monkeypatch.setattr(orch, "invalidate", _invalidate)
    monkeypatch.setattr(mut, "_emit", _emit)
    return calls


async def test_non_admin_rejected() -> None:
    with pytest.raises(mut.UnauthorizedAIOrchestrationMutationError):
        await mut.set_guild_orchestration(
            1, profile_key="balanced_helper", actor=_NON_ADMIN
        )


async def test_missing_actor_rejected() -> None:
    with pytest.raises(mut.UnauthorizedAIOrchestrationMutationError):
        await mut.set_guild_orchestration(1, profile_key="balanced_helper", actor=None)


async def test_unknown_key_rejected(_stub) -> None:
    with pytest.raises(mut.InvalidAIOrchestrationValueError):
        await mut.set_guild_orchestration(1, profile_key="bogus", actor=_ADMIN)
    assert _stub["writes"] == []  # nothing written on rejection


async def test_guild_write_invalidates_and_emits(_stub) -> None:
    result = await mut.set_guild_orchestration(
        1,
        profile_key="balanced_helper",
        actor=_ADMIN,
    )
    assert _stub["writes"] == [("guild", 1, "balanced_helper", 42)]
    assert _stub["invalidated"] == [1]
    assert _stub["emitted"] == ["ai.orchestration.guild_changed"]
    assert result.table == "ai_guild_policy"
    assert result.profile_key == "balanced_helper"
    assert result.generation == 5
    assert result.event_emitted is True


async def test_none_clears(_stub) -> None:
    result = await mut.set_channel_orchestration(
        1,
        3,
        profile_key=None,
        actor=_ADMIN,
    )
    assert _stub["writes"] == [("channel", 1, 3, None, 42)]
    # Channel/category bump generation separately.
    assert result.generation == 11
    assert result.target_id == 3
    assert _stub["emitted"] == ["ai.orchestration.channel_changed"]


async def test_category_write(_stub) -> None:
    result = await mut.set_category_orchestration(
        1,
        9,
        profile_key="no_tools",
        actor=_ADMIN,
    )
    assert _stub["writes"] == [("category", 1, 9, "no_tools", 42)]
    assert result.table == "ai_category_policy"
    assert result.target_id == 9
    assert _stub["emitted"] == ["ai.orchestration.category_changed"]


def test_known_profile_keys_exposed() -> None:
    keys = mut.known_profile_keys()
    assert "balanced_helper" in keys
    assert "compatible_default" in keys
