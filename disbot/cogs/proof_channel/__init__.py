"""Proof-channel subsystem package (Settings Phase 2 — Batch 4 tail).

The cog itself stays at ``cogs/proof_channel_cog.py`` (renaming a loaded
extension is its own migration); this package holds the subsystem's
declared configuration so the binding / provisioning / settings
catalogues can discover it.

Modules:
    schemas — the ``proof_channel`` :class:`SubsystemSchema` (the
              ``proof_channel`` binding + the OPTIONAL ``#proof``
              resource requirement), registered from
              ``ProofChannelCog.cog_load``.
"""
