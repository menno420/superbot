"""Unit tests for the image-moderation config read model."""

from __future__ import annotations

import pytest

from services import image_moderation_config
from services.image_moderation_config import ImageModerationPolicy


def test_any_category_enabled():
    assert not ImageModerationPolicy(enabled=True).any_category_enabled
    assert ImageModerationPolicy(enabled=True, sexual_enabled=True).any_category_enabled
    assert ImageModerationPolicy(enabled=True, hate_enabled=True).any_category_enabled


def test_defaults_are_all_off():
    pol = ImageModerationPolicy()
    assert pol.enabled is False
    assert not pol.any_category_enabled
    assert pol.threshold_percent == 80


def test_exemption_helpers():
    pol = ImageModerationPolicy(
        exempt_role_ids=frozenset({10, 20}),
        exempt_channel_ids=frozenset({99}),
    )
    assert pol.is_exempt_channel(99) is True
    assert pol.is_exempt_channel(1) is False
    assert pol.is_exempt_channel(None) is False
    assert pol.is_exempt_member({5, 20}) is True
    assert pol.is_exempt_member({5, 6}) is False


@pytest.mark.asyncio
async def test_load_policy_composes_typed_values(monkeypatch):
    stored = {
        "enabled": True,
        "sexual_enabled": True,
        "threshold_percent": 90,
        "exempt_roles": "10, 20",
        "exempt_channels": "30",
    }

    async def fake_resolve(guild_id, subsystem, name, fallback):
        assert subsystem == "image_moderation"
        return stored.get(name, fallback)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    pol = await image_moderation_config.load_policy(guild_id=123)
    assert pol.enabled is True
    assert pol.sexual_enabled is True
    assert pol.threshold_percent == 90
    assert pol.exempt_role_ids == frozenset({10, 20})
    assert pol.exempt_channel_ids == frozenset({30})
    # Unset fields fall back to the canonical defaults.
    assert pol.violence_enabled is image_moderation_config.DEFAULT_VIOLENCE_ENABLED
    assert pol.hate_enabled is image_moderation_config.DEFAULT_HATE_ENABLED
