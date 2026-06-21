# Reconciliation pass — 2026-06-20 · the band-#1200 Q-0107 cadence pass

> **Status:** `historical` — the docs-only review + planning pass for the band that crossed **#1200**
> (cadence = every **30th** merged PR per Q-0134; `#1200 = 30 × 40`; previous cadence pass
> [the band-#1170 pass](reconciliation-pass-2026-06-20-band1170.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1202**
> (`.github/workflows/reconciliation-trigger.yml`) — the **fifteenth** consecutive real cadence fire
> and live proof the loop self-fires: #1202 was authored by **`menno420`** (the `ROUTINE_PAT` owner),
> not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed + control-plane
> · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker → **#1201**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**Merged since the band-#1170 pass (band #1172–#1201).** Two bands of reconciliation ran on the same
day (2026-06-20) at high velocity; this is the second. The band's headline is a **new creature-catch/PvP
game** stood up entirely as design+sim+catalog+combat (no runtime cog yet), alongside a Pokétwo/MusicBot
research lane, a CI PR-guard determinism sweep, and the Claude-Design bot-site build-out.

- **NEW creature-catch/PvP game — design + sim + catalog + combat (#1183 · #1185 · #1193 · #1194).** An
  original-IP (no Pokémon names) creature game built as design+tooling+data: a stdlib deterministic
  Monte-Carlo **playability simulator** (`tools/game_sim/creature_battle_sim.py`, verdict **PLAYABLE**,
  surfaced the core design rule *PvP must be level-normalized*), the v1 ruleset + the copyright answer
  (#1183), creature roster sizing + legal music-bot findings (#1185), a data-driven **36-creature catalog**
  sim-validated playable (#1193), and the **complete combat model** — moves / damage types / 6v6 (#1194).
  No `disbot/` cog yet — the runtime build is the next buildable lane (Q-0187;
  [plan](creature-game-design-and-sim-2026-06-20.md)).
- **Pokétwo + MusicBot research → feature-mapping plan + BUG-0019 (#1180 · #1182).** A research report → a
  feature-mapping plan ([plan](poketwo-musicbot-feature-mapping-plan-2026-06-20.md), #1180); **BUG-0019**
  capture (the AI replied to *other bots'* mentions) + the Pokétwo demand signal (#1182). (BUG-0019 #2 —
  the `@everyone`/`@here` false-personal-ping leg — shipped as #1186, already in the prior band's ledger.)
- **CI PR-guard determinism (#1187 · #1188 · #1191).** The pr-conflict-guard now uses a deterministic
  `git merge-tree` (kills the "only occasionally red" flake, #1187); pr-auto-update gets the same
  deterministic behind-detection fix for the identical async race (#1188); both were then extracted onto
  **one shared, unit-tested git merge-state helper** (#1191).
- **Claude-Design bot-site (#1175 · #1176 · #1178 · #1196 · #1198 · #1199).** Full landing-page composition
  (#1175), GitHub-connector design-workflow docs (#1176), composing the rest of the site (Features /
  Commands / Changelog / Status, #1178), serving the SPA with a **live generated data layer** (#1196), a
  plain-language website explainer + the Claude Design loop (#1198), and the plan to migrate the live
  bot-site onto the React design-system app ([plan](botsite-react-spa-migration-plan-2026-06-20.md), #1199).
- **Mining/community fix + consistency-linter (#1177 · #1189).** `!character` now shows the paper-doll +
  missing back buttons added (#1177); the consistency-linter `back_button` rule now also catches
  dynamically-built (`add_item`) hubs (#1189).
- **Workflow tooling (#1174 · #1181 · #1192 · #1195).** `check_loop_health.py` gained the `gh`-absent
  stdlib-REST fallback (#1174); the **band PR-status classifier + Recently-shipped trim actuator** shipped
  (#1181 — `scripts/band_pr_status.py` + `scripts/trim_recently_shipped.py`, both used by this pass and
  building the band-#1170 pass's Q-0089 idea); a SessionStart branch-freshness warning (#1192, Q-0188);
  re-landed a dropped status-move decision (#1195, born-red slip).
- **Dependabot + dashboard generated-data refresh band (#1172 · #1179 · #1184 · #1190 · #1201).** A
  dependabot design-system npm bump (#1172) + the per-source-merge `dashboard-data-refresh` cadence regen of
  `dashboard/data/dashboard.json` (#1179 · #1184 · #1190 · #1201, Q-0167).

**Ledger reconciled:** `check_current_state_ledger --strict` flagged 25 merged PRs newer than the #1170
marker (benign-lag class). All of #1172–#1201 were absent from the live ledger; recorded as eight grouped
Recently-shipped entries, then trimmed the live list back to the 20 newest with the new
`scripts/trim_recently_shipped.py` actuator (which moved #1129 · #1126 · #1125 · #1124 · #1115 · #1109 ·
the #1112-band · the #1101-band to `current-state-archive.md`). `--strict` green afterward;
`check_docs --strict` green.

**Control-plane reconciled (Q-0135):** `check_loop_health.py` reported SKIP (`gh`/`GITHUB_TOKEN`
unavailable in-container — the recurring mode the #1174 fallback addresses for next time), so the live read
was done via the trigger-issue author — **#1202 authored by `menno420`** confirms `ROUTINE_PAT` is set + the
loop self-fires. Added #1202 to the canonical control-plane table row 1
(`operations/autonomous-routines.md`) — fifteenth consecutive self-fire.

**Dashboard freshness:** `check_dashboard_data --drift` reported **OK ✓ (0 warnings, 45 cogs)** — no
structural identifier drift this band — and `export_dashboard_data.py` was re-run for cadence freshness.

### Open-PR disposition (Q-0125)

| PR | State | Disposition |
|---|---|---|
| #1200 (botsite: sync app.js/app.css verbatim from the Claude-Design handoff) | open | **Left** — the **owner's** PR (authored by `menno420`), purely additive design-owned files copied verbatim, CI green (`conflict-guard` success; `botsite/` changes don't trip Code Quality). Not a `claude/*` session PR and not stale — the owner's to land. |

The dependabot python-minor-patch dev-group PR (#1074) carried in prior passes appears **no longer open** in this read (only #1200 returned by `list_pull_requests state=open`) — likely closed/superseded by the design-system npm bumps; nothing to do.

## 2. Band scorecard (vs. the band-#1170 next-band queue)

The band-#1170 §3 queue ranked: (1) consistency-linter AI-nav PR 1, (2) procedures→skills Batch 2,
(3) `check_loop_health.py` gh-absent fallback (promoted that pass), (4) the ungated stdlib-guard cluster,
(5) owner-directed product ideas. **Consumption:** the **loop-health gh-fallback shipped** (#1174, the
promoted plan), and the **band PR-status classifier + Recently-shipped trim actuator shipped** (#1181 —
the band-#1170 pass's own Q-0089 idea). The two big `needs-hermes-review` lanes (AI-nav PR 1, procedures→skills
Batch 2) are **not yet started** (both need a runtime/CLAUDE.md-editing session). **Off-queue but high-value:**
the band instead opened a *new product lane* (the creature game, owner-directed Q-0187) and a CI-determinism
sweep — both genuine, neither was on the ranked queue, which is healthy (the owner drives product direction).

## 3. Pruned / fixed this pass + control-plane

- Reset the `Last reconciliation pass` marker #1170 → **#1201**; next due at **#1230** (`1201 // 30 == 40`,
  so no re-fire until a merge crosses into band 41).
- Added #1202 to the control-plane ROUTINE_PAT row (fifteenth consecutive self-fire).
- Trimmed the live Recently-shipped ledger to 20 with the new actuator; **hand-corrected its buggy floor
  pointer** (it wrote `#1170 … #1` from stray prose matches; true span `#1129 … #535`) and filed
  **[BUG-0020](../health/bug-book.md)** for the proper script fix (needs a test → a dispatch run, not this
  docs-only pass).
- Took a first prune-cut at the `current-state.md` ▶ Next action callout's accreting band-history (prepended
  the seventeenth-pass line; the band-#1170 Q-0102 review's "dedicated aggressive trim" recommendation still
  stands as its own ungated session).
- Regenerated `dashboard/data/dashboard.json` (cadence freshness; no structural drift).
- **Runtime bugs noticed this pass:** none new (BUG-0019 #1 stays the open owner-design fork from the prior
  band; BUG-0020 is tooling, recorded above).

## 4. The next band (depth to #1230)

**Depth check: ~16–20 genuine buildable slices — well over the 15 threshold, so NO `⚠️ PLAN-BACKLOG-THIN`
flag.** The creature-game v1 runtime lane is a multi-PR initiative on its own (catch → collection/dex → PvP
battle → leaderboards), and on top of it sit the botsite-React migration, the consistency-linter AI-nav
clear-down, procedures→skills Batch 2, and the remaining stdlib guard. **Honest caveat (carried, unchanged):**
the *cleanly-ungated self-merge* subset is thinner than the headline count — most of the deepest lanes are
runtime / `needs-hermes-review` (creature-game cog, AI-nav, CLAUDE.md-editing batches), so an empty *autonomous*
fire should prefer a substantial review-gated lane or promote a fresh idea → plan → build (Q-0172) over a
marginal guard.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Creature-game v1 — catch + collection/dex cog** | `plan-first` | The design/sim/catalog/combat all shipped this band; build the `disbot/cogs/` catch flow + collection/dex first (read-mostly, additive). [plan](creature-game-design-and-sim-2026-06-20.md). |
| A2 | **Creature-game v1 — PvP battle cog** | `plan-first` | Level-normalized per the sim's core finding; runtime, wants a Q-0086 live-walk + `needs-hermes-review`. |
| A3 | **Creature-game — leaderboards + reuse `game_xp`** | `plan-first` | Reuses the shared game-XP service like fishing/mining; additive. |
| B1 | **botsite React-SPA migration** | `plan-first` | [plan](botsite-react-spa-migration-plan-2026-06-20.md) — migrate the live bot-site onto the design-system React app. |
| C1 | **Consistency-linter AI-nav PR 1** | `plan-first` | [plan](ai-panel-inplace-navigation-plan-2026-06-19.md); clears the 17 `views/ai/` `edit_in_place` findings, then graduates the rule. Runtime/Q-0086, `needs-hermes-review`. |
| C2 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → `needs-hermes-review`. |
| D1 | **`public-data-contract-field-snapshot` guard** | `ready` | The last ungated stdlib guard candidate from the prior band's cluster. |
| D2 | **Fix BUG-0020** (`trim_recently_shipped.py` floor pointer) | `ready` | Recompute the span from leading bullet ids only; add a `tests/unit/scripts/` regression — a dispatch run (touches a script + test). |
| E1 | **Pokétwo/MusicBot mapped features** | `plan-first` | From the #1180 feature-mapping plan, as the owner greenlights individual rows (music has the #1185 legal findings to respect). |

Gated/owner-paced (not in the buildable count): website rollout (provision `botsite/` + submissions DB,
domain cutover) · feedback-board PR 1 (owner dashboard auth) · the AI-ticket build (Q-0183, own session) ·
Explore-hub PR 2 + the gated layers (Q-0182) · dashboard writes / control-API (security review) ·
creature-game PvP balance + art (Q-0187) · fishing follow-ons (Q-0175) · BTD6 floors (exhausted).

## 5. The idea + the previous-pass review + the system improvement

**The Q-0089 idea this pass added:**
[`reconcile-pass-tail-trim-actuator`](../ideas/reconcile-pass-tail-trim-actuator-2026-06-20.md) — the
`current-state.md` ▶ Next action callout grows by one band-history sentence every pass and is now a wall of
consumed history fighting its own "read THIS line" purpose (the standing Q-0102 finding). The trim actuator
that *was* built this band handles the Recently-shipped *list*; the ▶ Next action *callout* has no equivalent.
The idea: a small stdlib helper (or a `--callout` mode of the existing trimmer) that moves any "Nth Q-0107
PASS DONE" sentence older than the **two** most recent passes out of the live callout into its already-existing
per-band pass record, leaving a one-line pointer — making the documented "aggressive prune" deterministic
rather than a per-pass judgment call.

**⟲ Previous-pass review (Q-0102):** the band-#1170 pass was strong and self-consistent — it promoted the
loop-health fallback to a plan **and** filed the trim-actuator Q-0089 idea, **both of which shipped in this
very band** (#1174, #1181), which is the self-improvement loop working exactly as designed (idea → plan →
build across one band). **What it missed / where this pass corrected it:** it did not foresee that its own
trim actuator would mis-write the floor pointer on first use — understandable (it filed the *idea*; the build
was #1181) — but it is a reminder of the Q-0105 discipline that a brand-new actuator's output must be
ground-truthed before trust (this pass did, caught it, filed BUG-0020). **The durable improvement (initiated,
not waited-for):** the actuator's docstring already *called* the floor pointer "the fragile part" yet the
implementation matched all `#N` in prose — a checker/actuator that documents its own fragile spot should
**carry a self-test for exactly that spot in the same PR** (BUG-0020's stays-fixed guard is that test). More
broadly, the ▶ Next action callout bloat is now a multi-pass-standing finding with an idea filed but no build;
it should be promoted to a real slice (D-class above is close) rather than re-noted each pass.
