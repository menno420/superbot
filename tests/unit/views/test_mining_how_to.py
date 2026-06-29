"""Mining How-to panel — completion-cert punch-list #1 (Q-0209).

Pins the dedicated 📖 How-to affordance at the mining hub: the hub exposes a
``mining:how_to`` button, and the How-to panel is a static guide that returns to the
mining hub via a "↩ Mining Hub" back button (not a dead-end terminal — #1529).
"""

from __future__ import annotations

import discord

from views.mining.how_to_panel import MiningHowToView, build_how_to_embed
from views.mining.main_panel import MiningHubView


def test_hub_exposes_how_to_button():
    view = MiningHubView()
    ids = [getattr(c, "custom_id", None) for c in view.children]
    assert "mining:how_to" in ids


def test_how_to_embed_is_a_one_screen_guide():
    embed = build_how_to_embed()
    assert embed.title and "How mining works" in embed.title
    # The guide covers the core loop's top actions so a new player isn't lost.
    desc = embed.description or ""
    for cue in ("Mine", "Harvest", "Gear", "Workshop", "Character"):
        assert cue in desc, f"how-to guide should mention {cue!r}"


def test_how_to_view_has_back_to_mining_hub_not_a_dead_end():
    """The panel carries a back button (a nav-carrying return), so it is not a
    trapped terminal view (the #1529 no_dead_end class)."""
    view = MiningHowToView(author=_FakeUser(), guild_id=123)
    labels = [getattr(c, "label", "") for c in view.children]
    assert any("Mining Hub" in (lbl or "") for lbl in labels)


class _FakeUser:
    id = 42
    display_name = "Miner"

    def __init__(self) -> None:
        pass
