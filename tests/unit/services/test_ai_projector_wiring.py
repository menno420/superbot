"""Regression tests for the AI settings → typed-policy projector wiring.

The AI subsystem mirrors its legacy KV scalars (provider, model, master
switch, level, cooldown, ...) into the typed ``ai_guild_policy`` table via
a post-write projector registered with the settings mutation pipeline.
That projector has to be *registered at startup* or every AI settings
change saves the legacy scalar but never updates the typed row the gateway
and resolver actually read — so the change appears to save but does
nothing. These tests pin the registration so it can't silently regress.
"""

from __future__ import annotations

import pytest

from services import settings_mutation
from utils.settings_keys import AI_DEFAULT_PROVIDER


@pytest.fixture(autouse=True)
def _isolate_projectors():
    saved = dict(settings_mutation._PROJECTORS)
    settings_mutation._PROJECTORS.clear()
    yield
    settings_mutation._PROJECTORS.clear()
    settings_mutation._PROJECTORS.update(saved)


def test_ai_schema_registration_wires_the_projector():
    """Registering the AI schema (done at cog load) must also wire the
    projector, otherwise settings changes never reach the typed table."""
    from cogs.ai.schemas import register_schemas

    register_schemas()

    assert "ai" in settings_mutation._PROJECTORS, (
        "AI post-write projector not registered — provider/model/etc. "
        "settings changes will save to the legacy KV but never project "
        "into ai_guild_policy."
    )


@pytest.mark.asyncio
async def test_ai_setting_change_projects_into_typed_policy(monkeypatch):
    """End to end: an AI provider change flows through the pipeline and
    upserts the typed ai_guild_policy.default_provider column."""
    from cogs.ai.schemas import register_schemas

    register_schemas()

    saved: dict = {}

    async def fake_set_setting(guild_id, key, value):
        pass

    async def fake_audit(guild_id, key, value, *, actor_id=None):
        pass

    async def fake_get_setting(guild_id, key, default=None):
        return {AI_DEFAULT_PROVIDER: "anthropic"}.get(key, default)

    async def fake_db_set_guild_policy(guild_id, **fields):
        saved["guild_id"] = guild_id
        saved.update(fields)

    monkeypatch.setattr("utils.db.settings.set_setting", fake_set_setting)
    monkeypatch.setattr(settings_mutation, "_emit_audit", fake_audit)
    monkeypatch.setattr("utils.db.settings.get_setting", fake_get_setting)
    monkeypatch.setattr("utils.db.ai.set_guild_policy", fake_db_set_guild_policy)

    await settings_mutation.apply_setting_change(
        123, "ai", AI_DEFAULT_PROVIDER, "anthropic",
    )

    assert saved.get("guild_id") == 123
    assert saved.get("default_provider") == "anthropic"
