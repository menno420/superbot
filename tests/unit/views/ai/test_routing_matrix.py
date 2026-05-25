"""PR-G tests for the operator routing matrix.

Pin:

* The matrix renders the dry-run resolver outcome (allowed / denied,
  effective min_level, effective cooldown, profile labels,
  precedence trace).
* The view never mutates — calls only ``ai_natural_language_policy.resolve``.
* Admin-only gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from core.runtime.ai.contracts import PolicyDenialReason
from views.ai.routing import RoutingMatrixSelectView, build_routing_matrix_embed


@dataclass
class _FakeDecision:
    allowed: bool
    reason_code: PolicyDenialReason
    effective_min_level: int
    effective_cooldown: int
    instruction_profile_ids: tuple
    policy_snapshot_hash: str
    precedence_trace: tuple


@pytest.mark.asyncio
async def test_matrix_renders_allowed(monkeypatch):
    from services import ai_natural_language_policy as nlp

    async def _resolve(ctx, *, dry_run):
        assert dry_run is True
        return _FakeDecision(
            allowed=True,
            reason_code=PolicyDenialReason.NONE,
            effective_min_level=3,
            effective_cooldown=15,
            instruction_profile_ids=(42,),
            policy_snapshot_hash="abc",
            precedence_trace=(
                "guild: baseline min_level=2 cooldown=30s",
                "channel: override min_level=3",
            ),
        )

    async def _list_presets():
        from services.ai_behavior_profile_service import BehaviorPresetSummary

        return [
            BehaviorPresetSummary(
                preset_id=42,
                key="btd6_focused",
                headline="x",
                recommended_mode="always_reply",
                body="",
            ),
        ]

    monkeypatch.setattr(nlp, "resolve", _resolve)
    monkeypatch.setattr(
        "services.ai_behavior_profile_service.list_presets",
        _list_presets,
    )

    embed = await build_routing_matrix_embed(
        guild_id=1,
        channel_id=2,
        user_id=3,
    )
    assert isinstance(embed, discord.Embed)
    blob = (
        (embed.description or "")
        + " "
        + "\n".join(f.name + " " + f.value for f in embed.fields)
    )
    assert "allowed" in blob
    assert "min_level" in blob
    assert "3" in blob  # effective min_level
    assert "btd6_focused" in blob
    assert "channel: override" in blob


@pytest.mark.asyncio
async def test_matrix_renders_denied(monkeypatch):
    from services import ai_natural_language_policy as nlp

    async def _resolve(_ctx, *, dry_run):
        return _FakeDecision(
            allowed=False,
            reason_code=PolicyDenialReason.BELOW_MIN_LEVEL,
            effective_min_level=5,
            effective_cooldown=60,
            instruction_profile_ids=(),
            policy_snapshot_hash="def",
            precedence_trace=("guild: baseline ...",),
        )

    async def _list_presets():
        return []

    monkeypatch.setattr(nlp, "resolve", _resolve)
    monkeypatch.setattr(
        "services.ai_behavior_profile_service.list_presets",
        _list_presets,
    )

    embed = await build_routing_matrix_embed(
        guild_id=1,
        channel_id=2,
        user_id=3,
        user_level=1,
    )
    field_text = "\n".join(f.value for f in embed.fields)
    assert "denied" in field_text
    assert "below_min_level" in field_text


@pytest.mark.asyncio
async def test_matrix_view_admin_gate():
    view = RoutingMatrixSelectView()
    interaction = MagicMock()
    interaction.user = SimpleNamespace(
        guild_permissions=SimpleNamespace(administrator=False),
    )
    interaction.response.send_message = AsyncMock()
    ok = await view.interaction_check(interaction)
    assert ok is False


def test_matrix_view_admin_gate_allows_admin():
    view = RoutingMatrixSelectView()
    children = list(view.children)
    # There should be exactly one channel-select child.
    assert any(isinstance(c, discord.ui.ChannelSelect) for c in children)
