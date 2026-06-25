"""Server-scan snapshot cache helpers (section retired in PR 3a).

The interactive "Scan server" section was a read-only step in the old
section-list wizard; PR 3a retired it from the flow (its function now
lives in Essential Setup's step 0 + "Check my setup"). What remains is
the per-hub snapshot cache used by sibling sections: ``channels`` still
imports :func:`get_cached_snapshot` to pre-fill its classifier hints when
a snapshot was attached to the hub view. With the scan button gone the
cache is simply never populated, and ``channels`` already degrades
gracefully to ``None`` (its hints just do not appear), so these helpers
stay as the stable seam.

PR 3b follow-up: once the Advanced editor rework lands, ``channels`` can
drop its snapshot lookup entirely and this module can go with it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from services.guild_snapshot import GuildSnapshot

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

SLUG = "server_scan"

_CACHE_ATTR = "_cached_snapshot"


def set_cached_snapshot(hub: SetupHubView, snapshot: GuildSnapshot) -> None:
    """Attach ``snapshot`` to ``hub`` so sibling sections can read it.

    The attribute name is shared with :func:`get_cached_snapshot`. A
    fresh wizard launch creates a fresh hub view with no cached snapshot,
    which is the desired behaviour.
    """
    setattr(hub, _CACHE_ATTR, snapshot)


def get_cached_snapshot(hub: SetupHubView) -> GuildSnapshot | None:
    """Return the cached snapshot for ``hub`` or ``None`` if absent."""
    return getattr(hub, _CACHE_ATTR, None)


__all__ = [
    "SLUG",
    "get_cached_snapshot",
    "set_cached_snapshot",
]
