"""Regression: role/XP panels must not collide with discord.py internals.

discord.py 2.7 (components-v2) ships two internals these panels previously
shadowed — both reachable only at runtime, so the mocked unit tests missed them:

* ``discord.ui.View._refresh(components)`` is called on every MESSAGE_UPDATE.
  A panel defining its own ``_refresh(self)`` shadowed it; discord.py then
  called the override with the components list and the 1-arg signature raised
  ``TypeError`` **inside the gateway poll loop**, crashing the whole bot. The
  panels' re-render helper is now ``_rerender``.
* ``discord.ui.Item.parent`` is a read-only property. A ``Select`` subclass
  doing ``self.parent = parent`` raised ``AttributeError: can't set attribute``
  the moment it was constructed (i.e. the Remove / Delete dropdowns). The panel
  reference is now stored as ``self._panel``.

Both regressions entered via the unpinned ``discord.py>=2.3.0`` (requirements.txt)
resolving to 2.7.x in a fresh install.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock


def test_panels_do_not_shadow_view_refresh():
    from views.roles.time_roles_panel import TimeRolesPanel
    from views.roles.xp_roles_panel import XpRolesPanel

    for panel in (TimeRolesPanel, XpRolesPanel):
        # Defining _refresh shadows discord.ui.View._refresh(components) and
        # crashes the bot on MESSAGE_UPDATE — the panel must not own one.
        assert "_refresh" not in vars(panel), f"{panel.__name__} shadows View._refresh"
        assert "_rerender" in vars(panel), f"{panel.__name__} lost its _rerender helper"


def test_remove_and_delete_selects_construct_without_parent_collision():
    # discord.ui.Item.parent is read-only in discord.py 2.7; a select that
    # assigned self.parent raised AttributeError at construction time.
    from views.roles.management_panel import _DeleteRoleSelect
    from views.roles.time_roles_panel import _TimeRemoveSelect
    from views.roles.xp_roles_panel import _XpRemoveSelect

    panel = MagicMock()
    role = SimpleNamespace(id=7, name="Veteran")

    drs = _DeleteRoleSelect(panel, [role])
    assert drs._panel is panel

    trs = _TimeRemoveSelect(panel, [{"role_name": "Veteran", "days_required": 30}])
    assert trs._panel is panel

    xrs = _XpRemoveSelect(panel, [{"role_name": "Veteran", "level_required": 5}])
    assert xrs._panel is panel
