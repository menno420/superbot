"""Tests for btd6 stats embed rendering against real committed data."""

from __future__ import annotations

import pytest

from services import btd6_stats_service as svc
from utils.btd6.stats_embed import (
    build_pro_tier_embed,
    format_normal_stats,
    tier_label,
)


@pytest.fixture(autouse=True)
def _fresh():
    svc.reset_cache()
    yield
    svc.reset_cache()


def test_format_normal_stats_base_bomb():
    stats = svc.get_tower_stats("bomb_shooter")
    text = format_normal_stats(svc.normal_stats(stats.tier("000")))
    assert "1** dmg" in text or "1 dmg" in text.replace("*", "")
    assert "Explosion" in text
    assert "22" in text
    assert "1.5s cooldown" in text
    assert "can't see Camo" in text


def test_tier_label_uses_upgrade_names():
    stats = svc.get_tower_stats("bomb_shooter")
    assert tier_label(stats, "000") == "Base (0-0-0)"
    assert tier_label(stats, "500") == "Bloon Crush (5-0-0)"
    assert tier_label(stats, "040") == "MOAB Assassin (0-4-0)"


def test_pro_embed_bloon_crush():
    stats = svc.get_tower_stats("bomb_shooter")
    embed = build_pro_tier_embed(stats, "500")
    assert "Bloon Crush" in embed.title
    blob = "\n".join(f.value for f in embed.fields)
    assert "24 dmg (Normal)" in blob
    assert "Stun 2s" in blob
    assert "knockback" in blob.lower()


def test_pro_embed_ability_tier():
    stats = svc.get_tower_stats("bomb_shooter")
    embed = build_pro_tier_embed(stats, "005")  # Bomb Blitz — Bomb Storm ability
    names = [f.name for f in embed.fields]
    assert any("Ability" in n for n in names)
    blob = "\n".join(f.value for f in embed.fields)
    assert "BADs/Bosses" in blob


def test_pro_embed_economy_tower_has_no_combat_fields():
    farm = svc.get_tower_stats("banana_farm")
    embed = build_pro_tier_embed(farm, "000")
    assert embed.fields == []
    assert "economy" in (embed.description or "").lower()
