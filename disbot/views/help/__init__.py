"""Help-appearance editor views (audit Phase 5 — PR A).

Operator UI over the HLP-3 overlay store: hide / rename / re-describe
hubs and subsystems in Help. Every write goes through the audited
:mod:`services.help_overlay_mutation` seam; these views own zero policy.

Module:
    editor — the editor view stack (home → entity picker → entity editor).
"""
