"""Fishing views — the interactive minigame panels (owner design Q-0175).

PR1 ships the core ``cast → wait → BITE → reel`` loop
(:mod:`views.fishing.cast_view`). The tackle / fishdex / boat actions and the
trophy reel-fight layer on top in later slices, per
``docs/planning/fishing-minigame-design-2026-06-22.md``.
"""

from __future__ import annotations

from views.fishing.cast_view import FishingCastView, active_casts

__all__ = ["FishingCastView", "active_casts"]
