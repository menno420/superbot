"""Fishing views — the interactive minigame panels (owner design Q-0175).

PR1 ships the core ``cast → wait → BITE → reel`` loop
(:mod:`views.fishing.cast_view`). The tackle / fishdex / boat actions and the
trophy reel-fight layer on top in later slices, per
``docs/planning/fishing-minigame-design-2026-06-22.md``.
"""

from __future__ import annotations

from views.fishing.bait_shop import BaitShopView, build_bait_embed
from views.fishing.cast_view import FishingCastView, active_casts, prepare_cast
from views.fishing.menu import (
    FishingMenuView,
    build_fishlog_embed,
    build_menu_embed,
)
from views.fishing.rod_shop import RodShopView, build_rod_embed

__all__ = [
    "BaitShopView",
    "FishingCastView",
    "FishingMenuView",
    "RodShopView",
    "active_casts",
    "build_bait_embed",
    "build_fishlog_embed",
    "build_menu_embed",
    "build_rod_embed",
    "prepare_cast",
]
