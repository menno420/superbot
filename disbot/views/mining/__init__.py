"""Mining UI components (Phase S4.1 / Pattern B).

The PersistentView entry-point ``MiningHubView`` is hosted here per
``docs/architecture.md`` §"PersistentView placement" Pattern B (the cog
file is large; the view lives in views/ and the cog re-exports for
the persistent-view registry side-effect).

Importing this package triggers the ``@register`` decorator on
``MiningHubView`` so the persistent-view registry is populated before
``on_ready`` runs ``restore_anchors``.
"""

from views.mining.grid_mine_view import MineGridView  # noqa: F401 — re-exported
from views.mining.main_panel import MiningHubView  # noqa: F401 — re-exported
