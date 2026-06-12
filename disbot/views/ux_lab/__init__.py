"""UX Lab views — the interface-gallery wings (zero-write workbench).

Importing this package registers every exhibit's :class:`PatternSpec` in
``utils.ux_patterns.REGISTRY`` (wing modules register at import time).

Design: ``docs/planning/ux-lab-interface-gallery-plan-2026-06-12.md``.
"""

from views.ux_lab.buttons import ButtonsWingView
from views.ux_lab.compare import CompareView
from views.ux_lab.embeds import EmbedsWingView
from views.ux_lab.home import UxLabHomeView, build_home_embed, home_builder
from views.ux_lab.image_cards import ImageWingView
from views.ux_lab.layout_v2 import LayoutWingView
from views.ux_lab.mockups import MockupsWingView
from views.ux_lab.modals import ModalsWingView
from views.ux_lab.persistent_demo import UxLabPersistentDemo
from views.ux_lab.probes import ProbesBenchView
from views.ux_lab.selects import SelectsWingView

__all__ = [
    "ButtonsWingView",
    "CompareView",
    "EmbedsWingView",
    "ImageWingView",
    "LayoutWingView",
    "MockupsWingView",
    "ModalsWingView",
    "ProbesBenchView",
    "SelectsWingView",
    "UxLabHomeView",
    "UxLabPersistentDemo",
    "build_home_embed",
    "home_builder",
]
