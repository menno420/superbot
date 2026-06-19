# 2026-06-19 — Fleet A6: move governance exception types into utils/

> **Status:** `in-progress`

About to: move the governance exception classes into a new `utils/governance_exceptions.py` and repoint the `governance/` layer at it so it no longer imports `services` for the exception types (backward-compatible re-export kept for external importers).
