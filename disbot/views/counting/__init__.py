"""views.counting — counting-game admin hub.

Single panel exported as ``_CountingHubView`` (named with the
underscore prefix to match the legacy ``cogs.counting_cog`` import
surface; the cog re-exports it for back-compat).
"""

from __future__ import annotations

from views.counting.hub_panel import _CountingHubView

__all__ = ["_CountingHubView"]
