"""PR-B regression: ``upsert_profile`` refuses guild-scope preset writes.

Migration 044 seeds preset rows with ``guild_id IS NULL``,
``scope='system'``, ``is_preset=TRUE``. Guild operators must not be
able to author rows with ``is_preset=True``; they must also not be
able to overwrite a seeded preset row with ``is_preset=False`` via
a same-name upsert at scope='system'.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from services import ai_instruction_mutation
from utils.db import ai as ai_db


def _admin(actor_id: int = 1, *, administrator: bool = True):
    return SimpleNamespace(
        id=actor_id,
        guild_permissions=SimpleNamespace(administrator=administrator),
    )


@pytest.mark.asyncio
async def test_guild_actor_cannot_create_preset(monkeypatch):
    """Setting ``is_preset=True`` with a non-null ``guild_id`` is
    forbidden — that path would let any guild admin fabricate fake
    presets that the Behavior UI would surface to other guilds.
    """
    with pytest.raises(
        ai_instruction_mutation.UnauthorizedAIInstructionMutationError,
    ):
        await ai_instruction_mutation.upsert_profile(
            guild_id=42,
            name="evil_preset",
            body="impersonates a system preset",
            scope="guild",
            is_preset=True,
            actor=_admin(),
        )


@pytest.mark.asyncio
async def test_system_upsert_cannot_downgrade_existing_preset(monkeypatch):
    """A system-scope upsert with the same name as a seeded preset
    but ``is_preset=False`` would silently downgrade it. Refuse so
    the preset catalog stays trustworthy.
    """

    async def _fake_list(_guild_id, *, scope=None):
        return [
            {
                "id": 5,
                "guild_id": None,
                "name": "helpful_channel",
                "body": "...",
                "scope": "system",
                "feature_key": None,
                "is_preset": True,
            },
        ]

    monkeypatch.setattr(ai_db, "list_instruction_profiles", _fake_list)

    with pytest.raises(
        ai_instruction_mutation.UnauthorizedAIInstructionMutationError,
    ):
        await ai_instruction_mutation.upsert_profile(
            guild_id=None,
            name="helpful_channel",
            body="downgraded body",
            scope="system",
            is_preset=False,
            actor=_admin(),
        )


@pytest.mark.asyncio
async def test_normal_guild_profile_still_works(monkeypatch):
    """The guard above must not break ordinary guild-scope profile
    upserts that have ``is_preset=False``.
    """
    captured: dict = {}

    async def _fake_upsert(**kwargs):
        captured.update(kwargs)
        return 999

    async def _bump(_gid):
        return 1

    monkeypatch.setattr(ai_db, "upsert_instruction_profile", _fake_upsert)
    monkeypatch.setattr(ai_db, "bump_generation", _bump)
    monkeypatch.setattr(
        "services.ai_natural_language_policy.invalidate",
        lambda _gid: None,
    )

    result = await ai_instruction_mutation.upsert_profile(
        guild_id=10,
        name="custom",
        body="guild-authored body",
        scope="guild",
        actor=_admin(),
    )

    assert captured["guild_id"] == 10
    assert captured["name"] == "custom"
    assert captured["is_preset"] is False
    assert result.profile_id == 999
