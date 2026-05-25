"""AI policy management views (PR4A).

Admin UI for the typed AI policy tables (``ai_channel_policy``,
``ai_category_policy``, ``ai_role_policy``). All writes flow through
:mod:`services.ai_policy_mutation` so the existing event bus + cache
invalidation already emit and run; this package does not invent any
new audit surface.

Layout:

* :mod:`chooser` — entry-point ephemeral view shown when the admin
  clicks the Policy button on :class:`views.ai.panel.AIPanelView`.
* :mod:`channel_view` — channel-scope select + edit modal.

Category, role, and override-listing views land in follow-up commits
within this PR.
"""
