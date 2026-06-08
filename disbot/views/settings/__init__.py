"""Settings Manager views.

Browsing + scalar edit/reset surface for the platform's settings,
bindings, resource requirements, and recent audit history.
Mirrors the long-term UX shape documented in
``docs/setup-platform/operator-settings-presets.md``: a hub with a subsystem
dropdown, an overview/status header, and four diagnostic
sub-panels (Needs setup / Invalid settings / Missing bindings /
Recent changes).

S5 shipped the read-only navigation; S6 added scalar edit + reset
widgets; PR #7 added native channel/role selects and numeric
presets.  Today the subsystem drill-down can edit + reset every
declared scalar setting via the explicit allowlist of widget
files (see ``tests/unit/invariants/test_settings_cog_read_only.py``
for the allowlist and rationale).  Binding edit + resource
provisioning controls land in subsequent milestones; the cog
itself remains write-free at the import + AST level.
"""

from __future__ import annotations

__all__ = []
