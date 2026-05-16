"""views.economy — economy persistent panel + ephemeral sub-views.

Extracted from cogs/economy_cog.py during D5.

Modules:
    main_panel  — ``EconomyPanelView`` (PersistentView, SUBSYSTEM="economy")
    work_panel  — ``_WorkView`` / ``_JobSelect`` / ``_WorkSubView``
    shop_panel  — ``_ShopView`` / ``_ShopSelect`` / ``_ShopSubView`` /
                  ``_ShopPanelSelect``

The cog re-exports every name from this module so legacy
``from cogs.economy_cog import EconomyPanelView`` (and similar) keeps
resolving.  Importing this package is what triggers the @register
decorator that adds EconomyPanelView to ``persistent_views._REGISTRY``
— so the cog must import this package at module-load time (it does,
via ``from views.economy import EconomyPanelView, …``).
"""

from __future__ import annotations

from views.economy.main_panel import EconomyPanelView
from views.economy.shop_panel import (
    _ShopPanelSelect,
    _ShopSelect,
    _ShopSubView,
    _ShopView,
)
from views.economy.work_panel import _JobSelect, _WorkSubView, _WorkView

__all__ = [
    "EconomyPanelView",
    "_JobSelect",
    "_ShopPanelSelect",
    "_ShopSelect",
    "_ShopSubView",
    "_ShopView",
    "_WorkSubView",
    "_WorkView",
]
