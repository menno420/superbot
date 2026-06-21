# 2026-06-21 — Creature PvP: result recording + win/loss records + battle leaderboard

> **Status:** `complete` — PR #1257.

> **Run type:** `routine · dispatch`

## Arc

Empty scheduled dispatch fire. The ▶ Next action queue's startable lane (a) was the creature-game
**leaderboards slice (reuse `game_xp`, additive)** — #1230 had shipped the read-only PvP flow, and both
the plan §4 and `creature_battle_service`'s own docstring pointed at the deferred **audited-write half**
("the moment a battle records a result, this is where that transaction will live"). This run built that
half end-to-end and CI-verified it.

## What shipped (PR #1257)

- **migration `082_creature_battle_record.sql`** — per-(user, guild) win/loss tally; an empty table is
  byte-identical to the pre-PvP bot (the additive safety property, mirroring `creature_collection_log`).
- **`utils/db/games/creature_battles.py`** — transaction-aware CRUD: `record_battle_outcome`
  (winner +1W / loser +1L, two upserts on one conn), `get_battle_record`, `top_battlers` (wins>0,
  ordered wins↓ losses↑ user_id↑). Exported through `utils/db`.
- **`game_xp_service`** — new `battle_win` award (6 XP, `GAME_CREATURE`) through the one central award
  policy + daily soft-cap.
- **`creature_battle_service.resolve_and_record_pvp`** — resolves, then in ONE `db.transaction()`
  records both fighters' tally + awards the winner's XP + reads both updated records; emits the game-xp
  events **after** commit (Q-0071 contract, mirroring `creature_workflow.catch`). `resolve_pvp` stays
  the pure read path. New `RecordedPvp` dataclass carries the result + both records + the level-up note.
- **challenge view + renderer** — `build_result_embed` gained `records=`/`xp_note=`; the outcome embed
  now shows each fighter's updated W/L and any level-up notice.
- **`creature_battle_cog`** — `!cbattletop`/`!pvptop` (win ladder) + `!cbrecord`/`!battlerecord`
  (personal W/L + win rate).
- **tests** — `tests/unit/db/test_creature_battles_db.py` (SQL-shape pins),
  `test_creature_battle_service.py` (the audited-write seam: one-conn + post-commit emit, no-team
  short-circuit, level-up note), `test_creature_battle_render.py` (records field render + backward-compat).
- **docs de-staled** — plan §4 Battle bullet (flow + result-recording shipped), current-state ▶ Next
  action lane (a) marked buildable-complete for v1, `help-command-surface-map.md`. Regenerated the
  `site.json` / `dashboard.json` / `data.js` artifacts (the new commands changed the static scan).

## Findings / decisions

- **Decision made alone — self-merge, not `needs-hermes-review`.** My born-red card/PR initially framed
  this `needs-hermes-review` (the plan tagged the *PvP runtime* lane that way). But (1) the ▶ Next action
  lists this exact "leaderboards slice (reuse game_xp, additive)" as an **ungated** startable lane (a),
  distinct from the separate `needs-hermes-review` lane (c); (2) the owner **enabled auto-merge** on the
  PR mid-build; (3) it mirrors the established catch/fishing game-progression pattern exactly. So I let it
  self-merge on green and dropped the review label. (If this should have held for review, it's a clean
  one-PR revert — flag for the owner.)
- **Decision made alone — game progression is not `emit_audit_action`-audited.** The service docstring
  *anticipated* `emit_audit_action`, but the actual sibling (`creature_workflow.catch`) and
  `game_xp_service.award` do **not** audit-emit — audit is the moderation/settings/governance seam, not
  per-battle XP. I followed the real precedent (transaction + game-xp events, no audit) and corrected the
  docstring to say so.
- **Bug caught mid-build (mine):** first wrote the upsert SQL with a `$4/$5` numbering that left `$3`
  unreferenced — asyncpg can't type-infer an unused parameter ("could not determine data type of $3").
  Renumbered to `$1..$4` before it could ship. Also used `pool.fetchrow` (doesn't exist — the primitive
  is `pool.fetchone`).

## Context delta

- **Needed but not pointed to:** nothing new — `creature_workflow.catch` was the exact template (one
  transaction, conn-aware CRUD, post-commit events), and `game_xp_service.award` already took the
  workflow conn. The #1208/#1213/#1230 seams being clean is what made this a small additive slice.
- **Pointed to but didn't need:** the audit-emission read in the context map's recommended set — game
  progression doesn't audit (above).
- **Discovered by hand:** `pool` exposes `fetchone` (not `fetchrow`); adding bot commands drifts the
  committed `site.json`/`dashboard.json` (the BUG-0018/0023 generated-artifact class) → regen needed.
- **Weak point / unverified:** not live-walked — the full loop (challenge → resolve → record → embed →
  leaderboard) wants a runtime smoke on a real guild with two collections + Postgres (migration 082
  applies on deploy). The win-XP amount (6) is a taste constant, trivially retunable in `_AWARDS`.

## 📤 Run report

- **Did:** built the creature-PvP **result-recording + win/loss records + battle leaderboard** (the
  plan §4 audited-write half) on top of the #1230 read-only flow · **Outcome:** shipped (PR #1257,
  full CI mirror green, auto-merge armed)
- **Shipped:** #1257 — creature PvP result recording + records + `!cbattletop`/`!cbrecord` + `battle_win` xp
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none — but I self-merged rather than holding for review (see Findings);
  revert is one PR if undesired.
- **⚑ Owner manual steps:** none — merge auto-deploys; migration 082 applies on the deploy. No
  `!btd6ops seed-data`-style data step (no data file changed).
- **⚑ Self-initiated:** none — this was the dispatched ▶ Next action lane (a). (The merge-gate choice
  was a judgment call within it, flagged above.)
- **↪ Next:** creature-game PvP is **buildable-complete for v1**. Remaining creature slices are
  later/gated (Explore-hub Lane-B battle panel · balance + art Q-0187). The next **ungated** build is
  ▶ Next action lane (b) botsite React-SPA migration, (c) a `needs-hermes-review` lane
  (consistency-linter AI-nav PR 1 / procedures→skills Batch 2), or (d) promote a fresh idea (Q-0172).

## 💡 Session idea

**A `!cbattle` rematch button on the outcome embed.** The PvP flow ends with a static result embed; a
single "🔄 Rematch" button (re-issuing the same challenge with the players swapped as challenger) would
make laddering feel continuous instead of re-typing `!cbattle @x` each round — and it's a pure view
addition (reuse `CreatureBattleChallengeView`), no new service/DB. (Dedup-checked `docs/ideas/` — not
captured; the gradient-presets and reaction-role-audit ideas are unrelated.)

## ⟲ Previous-session review

The #1246 session (gradient-presets gallery) was a clean, well-scoped self-initiated increment and its
card was exemplary — but its own ⟲ review flagged that the modal-first-response docs rule *still* hasn't
been filed as a router Q-block, "again rather than filing unprompted." That's now been carried across at
least three sessions as a noted-but-never-filed item. **System improvement:** a durable rule an agent
can't self-apply (owner-governed file) shouldn't depend on each session *choosing* to file the router
Q-block — it evaporates every time. A tiny `scripts/` check that scans the newest `.sessions/` card for
"should be filed / router DISCUSS" phrasing and warns if no matching `Q-0NNN` block was appended would
turn "I noted it" into a CI-visible nudge, the same way the born-red gate turned "mark it ready" into a
hard step. (Not built this run — it's a workflow-tooling idea, captured here for grooming.)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#1257, auto-merge on green) |
| CI-red rounds | 1 real (4 generated-artifact freshness fails — regen'd; born-red HOLD otherwise) |
| Self-caught bugs pre-push | 2 (asyncpg `$3` gap · `pool.fetchrow`→`fetchone`) |
| New ideas contributed | 1 (rematch button) |
| Files touched | 8 runtime/test + 3 generated artifacts + 3 docs |
