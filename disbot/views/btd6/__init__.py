"""Views for the BTD6 Assistant cog.

PR 2 expanded the panel into a drill-down hub: clicking any button on
the public anchor now opens an ephemeral sub-view instead of mutating
the panel for everyone in the channel.
"""

from __future__ import annotations

from views.btd6.hero_browser_view import (
    HeroBrowserView,
    HeroDetailView,
    open_hero_browser,
)
from views.btd6.leaderboard_browser_view import (
    LeaderboardBrowserView,
    LeaderboardDetailView,
    LeaderboardKindListView,
    open_leaderboard_browser,
)
from views.btd6.live_events_view import (
    EventDetailView,
    LiveEventsBrowserView,
    open_live_events_browser,
)
from views.btd6.panel import BTD6PanelView, build_btd6_panel_embed
from views.btd6.tower_browser_view import (
    TowerBrowserView,
    TowerDetailView,
    open_tower_browser,
)

__all__ = [
    "BTD6PanelView",
    "EventDetailView",
    "HeroBrowserView",
    "HeroDetailView",
    "LeaderboardBrowserView",
    "LeaderboardDetailView",
    "LeaderboardKindListView",
    "LiveEventsBrowserView",
    "TowerBrowserView",
    "TowerDetailView",
    "build_btd6_panel_embed",
    "open_hero_browser",
    "open_leaderboard_browser",
    "open_live_events_browser",
    "open_tower_browser",
]
