# 2026-06-19 — Fleet B3: routine permission-surface lint

> **Status:** `in-progress`

About to: add `scripts/check_routine_permission_surface.py` + test — fail/warn when a routine-common command would resolve to a `permissions.ask` brake and silently stall an unattended run.
