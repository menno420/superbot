"""Fishing views — the interactive minigame panels (owner design Q-0175).

PR1 ships the core ``cast → wait → BITE → reel`` loop
(:mod:`views.fishing.cast_view`). The tackle / fishdex / boat actions and the
trophy reel-fight layer on top in later slices, per
``docs/planning/fishing-minigame-design-2026-06-22.md``.
"""

from __future__ import annotations

from views.fishing.bait_shop import BaitShopView, build_bait_embed
from views.fishing.boathouse import BoathouseView, build_boathouse_embed
from views.fishing.cast_view import FishingCastView, active_casts, prepare_cast
from views.fishing.dock import DockView, build_dock_embed
from views.fishing.fishery import FisheryView, build_fishery_embed
from views.fishing.menu import (
    FishingMenuView,
    build_fishlog_embed,
    build_menu_embed,
)
from views.fishing.rod_recipe_browser import RodRecipeBrowserView, build_recipe_panel
from views.fishing.rod_shop import RodShopView, build_rod_embed
from views.fishing.structures_hub import (
    StructuresView,
    build_structures_embed,
    open_structures_hub,
)
from views.fishing.tide_pool import TidePoolView, build_tide_pool_embed

__all__ = [
    "BaitShopView",
    "BoathouseView",
    "DockView",
    "FisheryView",
    "FishingCastView",
    "FishingMenuView",
    "RodRecipeBrowserView",
    "RodShopView",
    "StructuresView",
    "TidePoolView",
    "active_casts",
    "build_bait_embed",
    "build_boathouse_embed",
    "build_dock_embed",
    "build_fishery_embed",
    "build_fishlog_embed",
    "build_menu_embed",
    "build_recipe_panel",
    "build_rod_embed",
    "build_structures_embed",
    "build_tide_pool_embed",
    "open_structures_hub",
    "prepare_cast",
]
