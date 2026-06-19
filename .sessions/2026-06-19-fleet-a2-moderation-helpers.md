# 2026-06-19 — Fleet A2: move moderation _helpers into services/

> **Status:** `in-progress`

About to: move `cogs/moderation/_helpers.py` → `services/moderation_helpers.py` and rewrite the two importers (`moderation_cog.py`, `views/moderation/modals.py`) to import from `services.moderation_helpers`.
