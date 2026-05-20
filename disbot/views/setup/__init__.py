"""Setup-wizard views — Phase 9e and beyond.

This package holds every view that renders setup-wizard panels:

* ``provisioning/`` — Track 3 PR 7. Preview + confirm panels for the
  :class:`~services.resource_provisioning.ResourceProvisioningPipeline`.
* Future tracks add ``ai_review/``, ``hub.py``, ``readiness.py``,
  ``onboarding.py``, etc.

**Invariants enforced across this package** (pinned by tests under
``tests/unit/views/setup/``):

* No direct ``utils.db.*`` writes — views only call services.
* No direct ``guild.create_*`` calls — provisioning routes through
  the pipeline.
* Every view extends :class:`disbot.views.base.BaseView` (timeout +
  invoker-restriction defaults inherited).
"""
