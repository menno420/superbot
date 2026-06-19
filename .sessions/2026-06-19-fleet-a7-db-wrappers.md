# 2026-06-19 — Fleet A7: wrap raw SQL in utils/db helpers

> **Status:** `in-progress`

About to: move the 13 raw `pool.execute()/fetch*()` calls in `game_state_service.py` + `platform_consistency.py` behind named `utils/db/` helpers, behavior-preserving.
