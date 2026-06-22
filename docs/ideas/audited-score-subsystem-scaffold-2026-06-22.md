# Idea — "audited per-user score" subsystem scaffold + parity guard

> **Status:** `ideas` — capture, not a plan. **Subsystem:** none (agent-workflow / meta).
> Captured by the Karma planning session (2026-06-22): designing karma made it obvious that
> `economy`, `xp`, and now `karma` are the **same shape** repeated by hand.

## The pattern that keeps repeating

Every per-user *score* subsystem in this repo is built from the identical six pieces:
1. a `utils/db/<x>.py` low-level seam (upsert + RETURNING, an `insert_<x>_audit`),
2. an append-only `<x>_audit_log` table (migration),
3. a `services/<x>_service.py` single write seam (`give`/`award`/`credit` → audit → `bus.emit`),
4. a catalogue entry in `core/events_catalogue.py`,
5. an **INV** AST test forbidding DB writes outside the service (INV-F economy, INV-G xp, INV-K karma…),
6. a `RankProvider` in `services/rank_providers.py` so it shows on the leaderboard.

Building karma means hand-copying all six. Two cheap wins:

- **Scaffold** — a `scripts/new_score_subsystem.py <name>` (or extend the `new-subsystem` skill) that
  stamps the six files from the economy/xp template, pre-wired with the INV test and a rank provider
  stub. Makes the next reputation/streak/score subsystem a fill-in-the-blanks job and guarantees the
  two easy-to-forget pieces (the INV test + the leaderboard provider) are never skipped.
- **Parity guard** — a test that cross-checks: every table with a leaderboard-worthy per-user score
  column either has a `RankProvider` in `_PROVIDERS` **or** is on an explicit allow-list of
  intentional exclusions. Catches "shipped a new scoreboard with no leaderboard category" (the exact
  gap karma would have if PR 2's provider were forgotten).

Disposable (Q-0105): if the scaffold proves more friction than copy-paste over a couple of uses,
delete it — the parity guard is the higher-value half and should outlive the generator.
