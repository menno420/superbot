"""Settings Manager views — S5.

Read-only browsing surface for the platform's settings, bindings,
resource requirements, and recent audit history.  Mirrors the
long-term UX shape documented in
``docs/operator-settings-presets.md``: a hub with a subsystem
dropdown, an overview/status header, and four diagnostic
sub-panels (Needs setup / Invalid settings / Missing bindings /
Recent changes).

S5 is strictly read-only — no edit modals, no reset buttons that
write, no resource creation, no binding mutation, no
access-policy mutation.  S6 onward adds the write surfaces, gated
on the existing :class:`services.settings_mutation.SettingsMutationPipeline`
and :class:`services.binding_mutation.BindingMutationPipeline`.
"""

from __future__ import annotations

__all__ = []
