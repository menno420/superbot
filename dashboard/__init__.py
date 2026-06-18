"""SuperBot developer dashboard — a decoupled web app that renders generated JSON.

This package must never import ``disbot``; it reads only
``dashboard/data/dashboard.json`` (produced by
``scripts/export_dashboard_data.py``) plus, in later phases, the GitHub and
Railway APIs. See ``dashboard/README.md`` and
``docs/planning/developer-dashboard-plan.md``.
"""
