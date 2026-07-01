# 2026-07-01 — XP/level migration from other bots (Arcane)

> **Status:** `in-progress` — born-red card; flips to `complete` as the final step.

## Arc

Owner wants SuperBot to migrate chat XP/levels from another bot — the live case is
**Arcane**. Two possible sources: (1) a direct export/import method from the other bot,
or (2) scanning the level-up channel and copying the announced levels.

**Research finding (answers the owner's question):** Arcane has **no** direct
import/export API — imports *from* Arcane are not possible via their API (access is
restricted); the only exits are a browser-console scrape of the web leaderboard
(top-100 on free tier) or a manual export via Arcane support. So the **channel-scan**
path the owner proposed is the correct primary mechanism.

## Scope (this PR)

End-to-end XP-migration feature, admin-gated, preview-then-confirm, non-destructive:

- Pure parse + level math: `utils/xp_migration.py` (+ `total_xp_for_level` in `utils/db/xp.py`).
- Import primitive `db.set_imported_xp` (raise-only merge), wrapped by `xp_service.import_level`
  (respects INV-G — xp writes only via the service).
- Batch orchestration + audit + optional level-role sync: `services/xp_migration.py`.
- Confirmation panel `views/xp/import_panel.py`; `!xpimport` command in `xp_cog.py`
  reads the level-up channel history and opens the preview.
- Extensible announcer-format registry (Arcane / MEE6 / SuperBot / generic) + a documented
  seam for a future *direct* API provider (MEE6 has a public leaderboard API).
- Docs + unit tests.

_(Enders — context delta, telemetry, run report, idea, prev-session review — filled at close.)_
