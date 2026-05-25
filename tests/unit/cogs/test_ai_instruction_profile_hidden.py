"""PR-6 — ``ai_guild_instruction_profile`` is hidden from the primary
settings panel.

Pin: The auto-rendered subsystem settings panel (``!settings → AI``)
must NOT list the ``ai_guild_instruction_profile`` scalar. The
typed-table editor in the Behavior chooser is the authoritative
write path (see ``docs/ai-config-ownership.md`` § "Resolved
semantics" + § "Mutation seam").

The setting key is retained for backcompat KV reads — schema removal
would break the projection-trip tests.
"""

from __future__ import annotations

import pytest

from cogs.ai.schemas import AI_CONFIG_SCHEMA


@pytest.fixture(autouse=True)
def _register_ai_schema():
    """The AI schema is normally registered by ``AICog.cog_load``; in
    tests we register directly so :func:`get_schema('ai')` resolves."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(AI_CONFIG_SCHEMA)
    yield


def test_ai_guild_instruction_profile_is_hidden_from_panel():
    """The setting is flagged ``hidden_from_panel=True``."""
    spec = next(
        s for s in AI_CONFIG_SCHEMA.settings if s.name == "ai_guild_instruction_profile"
    )
    assert getattr(spec, "hidden_from_panel", False) is True


def test_other_ai_settings_remain_visible():
    """Every other AI setting stays visible in the auto-rendered panel."""
    hidden = [
        s.name
        for s in AI_CONFIG_SCHEMA.settings
        if getattr(s, "hidden_from_panel", False)
    ]
    assert hidden == ["ai_guild_instruction_profile"]


def test_hidden_specs_not_returned_by_editable_helper():
    """The editable-spec helper in the settings UI filters out hidden
    specs so the dropdown can't surface them."""
    from views.settings.subsystem_view import _editable_specs

    specs = _editable_specs("ai")
    names = {s.name for s in specs}
    assert "ai_guild_instruction_profile" not in names
    # A regular scalar that IS editable stays in the list.
    assert "ai_enabled" in names


@pytest.mark.asyncio
async def test_subsystem_embed_omits_hidden_scalar():
    """``!settings → AI`` rendered embed must not show the legacy
    free-text scalar — operators use the Behavior chooser modal."""
    from types import SimpleNamespace

    from views.settings.subsystem_view import _resolve_settings_block

    # Resolve in DM context (guild_id=None) — avoids the DB read path.
    lines = await _resolve_settings_block(None, "ai")
    blob = "\n".join(lines)
    assert "ai_guild_instruction_profile" not in blob
    # Cross-check a regular setting still renders.
    assert "ai_enabled" in blob
    del SimpleNamespace  # silence unused-import on some linters
