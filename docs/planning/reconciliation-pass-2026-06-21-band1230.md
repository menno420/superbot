# Reconciliation pass — 2026-06-21 · the band-#1230 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed **#1230**
> (cadence = every **30th** merged PR per Q-0134; `#1230 = 30 × 41`; previous cadence pass
> [the band-#1200 pass](reconciliation-pass-2026-06-20-band1200.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1232**
> (`.github/workflows/reconciliation-trigger.yml`) — the **sixteenth** consecutive real cadence fire
> and live proof the loop self-fires: #1232 was authored by **`menno420`** (the `ROUTINE_PAT` owner),
> not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed + control-plane
> · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker → **#1231**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**Merged since the band-#1200 pass (band #1203–#1231).** The band's headline is the **reaction-roles /
role-menu overhaul** (Carl-bot parity) shipped end-to-end, alongside the **creature game crossing from
design into runtime** (catch + collection, PvP engine), the **"free for everyone, forever" product North
Star** being codified, and a workflow-tooling sweep (permission-overlap guard, lane-overlap claim-scan,
fast-PR-open mandate).

- **Reaction-roles / role-menu overhaul (Carl-bot parity) (#1215 · #1216 · #1217 · #1218 · #1220 · #1219 ·
  #1227).** The plan (#1215 Carl-parity overhaul plan, #1216 UI direction = web dashboard vs in-Discord,
  #1217 presentation/editing §4.6, #1218 owner decisions locked + role-pickup analytics) then the build:
  **PR 1** audited `reaction_role_service` seam + `utils/db/role_menus` data layer + migration 078 + cog
  routing/teardown (#1220); **PR 2** the in-Discord role-menu builder (Surface B — buttons/selects/modals,
  #1219); **PR 3–5 together** (one owner-directed PR, Q-0191 merge-immediately, #1227) — per-message emoji
  modes [migration 079] · free temp-roles `RoleGrantsCog` + `!temprole` + `utils/duration` [migration 080] ·
  role-pickup analytics [migration 081]. Only **PR 6 (PIL banner cards) + the gated web builder (Surface A,
  control-API write side)** remain ([plan](reaction-roles-overhaul-plan-2026-06-21.md)).
- **Creature game — design → runtime (#1208 · #1213).** **Catch + collection/dex** shipped as the first
  runtime slice (#1208 — `disbot/cogs/creature_cog.py`, fishing-mirrored spine, `utils/creatures/` pure
  domain + `services/creature_workflow.py` audited write + migration 077 + the 36-creature catalog +
  `GAME_CREATURE` xp track), and the **level-normalized PvP battle engine** graduated into pure domain
  `disbot/utils/creatures/battle.py` (#1213, `needs-hermes-review`) with 24 fairness-gate tests. The
  **user-facing PvP flow is now IN FLIGHT** (#1230, born-red, `needs-hermes-review`) —
  [plan](creature-game-design-and-sim-2026-06-20.md) §4.
- **"Free for everyone, forever" product North Star (#1226 · #1228 · #1229 · #1231).** Codified the North
  Star (Q-0190, #1226), answered the open-source/self-host posture under it (#1228), and recorded the
  **license decision — stay MIT for now** (free-use-only deferred) (#1229/#1231). Owner-directed design
  decisions; also folded in the creature sim↔engine combat-constant parity guard (#1229).
- **Workflow tooling (#1211 · #1212 · #1223 · #1224 · #1225).** A **permission-overlap guard** + force-push
  ask-residual fix (#1212) on top of the `git push --force-with-lease` + `cd` allowlist (#1211); the
  **lane-overlap claim-scan** now reads the `active-work.md` claim ledger (#1223, `scripts/check_lane_overlap.py`);
  **Q-0189 — open the session PR fast (within ~2 min of start)** codified (#1224); pruned stale
  `active-work.md` claims (#1225).
- **Redaction guard — `public-data-contract-field-snapshot` (#1210).** The public `site.json` redaction guard
  now pins **leaf fields per family** (`SITE_FIELD_CONTRACT` in `export_dashboard_data.py` + the within-family
  whitelist in `check_dashboard_data.check_site_subset`), closing the within-family field-leak class so keys
  *and* leaves both fail closed — completing the ungated stdlib-guard cluster the prior bands tracked.
- **Bug fixes + CI/design-system (#1203 · #1205 · #1206 · #1207).** Recorded the Claude-Design connector as
  read-only (resolves the migration-plan Decision D, #1203); aligned Storybook deps on v10 to fix the
  design-system CI install (#1205); **BUG-0020** (`trim_recently_shipped.py` floor-pointer prose
  contamination) + **BUG-0021** (flaky lock-wait test) + **BUG-0022** (suite clobbers tracked `data.js`)
  root-fixed (#1206); **BUG-0023** botsite command-count reconcile + a tool-pin drift guard (#1207).
- **Dashboard generated-data refresh band (#1209 · #1214 · #1222).** The per-source-merge
  `dashboard-data-refresh` cadence regen of `dashboard/data/dashboard.json` (Q-0167).

**Ledger reconciled:** `check_current_state_ledger --strict` flagged 24 merged PRs newer than the #1201
marker (benign-lag class). All of #1203–#1231 were absent from the live ledger; recorded as seven grouped
Recently-shipped entries, then trimmed the live list back to the 20 newest (moving the older entries to
`current-state-archive.md`). `--strict` green afterward; `check_docs --strict` green.

**Control-plane reconciled (Q-0135):** `check_loop_health.py` reported SKIP (`gh`/`GITHUB_TOKEN`
unavailable in-container), so the live read was done via the trigger-issue author — **#1232 authored by
`menno420`** confirms `ROUTINE_PAT` is set + the loop self-fires. Added #1232 to the canonical
control-plane table row 1 (`operations/autonomous-routines.md`) — sixteenth consecutive self-fire.

**Dashboard freshness:** re-ran `export_dashboard_data.py` for cadence freshness;
`check_dashboard_data --drift` reported its structural-identifier state (recorded in the run report).

### Open-PR disposition (Q-0125)

| PR | State | Disposition |
|---|---|---|
| #1230 (Creature PvP battle flow — cog + views + read-service) | open | **Left** — a **live in-flight session** opened the same minute as the reconcile issue (15:08Z), born-red (session card `in-progress`), `needs-hermes-review`, runtime `disbot/` work. Not stale, not redundant, not mine to dispose — it is the named ▶ NEXT creature slice being built by another session. |

No stale or redundant `claude/*` PRs were open this pass (the prior band's #1200 owner PR has merged).

## 2. Band scorecard (vs. the band-#1200 next-band queue)

The band-#1200 §4 queue ranked: A1 creature catch+collection cog, A2 creature PvP cog, A3 creature
leaderboards, B1 botsite React migration, C1 consistency-linter AI-nav PR 1, C2 procedures→skills Batch 2,
D1 `public-data-contract-field-snapshot` guard, D2 fix BUG-0020, E1 Pokétwo/MusicBot features.
**Consumption:** **A1 shipped** (#1208 catch+collection), **A2 is half-shipped + in flight** (the engine
#1213 shipped, the user-facing cog is #1230 in review), **D1 shipped** (#1210), **D2 shipped** (#1206 —
BUG-0020 root-fixed, with BUG-0021/0022 as a bonus). The two big `needs-hermes-review` lanes (C1 AI-nav, C2
procedures→skills) are **still not started** (both want a runtime/CLAUDE.md-editing session). **Off-queue but
high-value:** the band's actual headline — the **reaction-roles overhaul** — was **not** on the ranked queue
at all (it was owner-directed product direction promoted mid-band, Q-0191), which is healthy: the owner drives
product, the queue tracks the autonomous backlog.

## 3. Pruned / fixed this pass + control-plane

- Reset the `Last reconciliation pass` marker #1201 → **#1231**; next due once merges cross **#1260**
  (`1231 // 30 == 41`, so no re-fire until band 42).
- Added #1232 to the control-plane ROUTINE_PAT row (sixteenth consecutive self-fire).
- **Executed the standing Q-0102 "aggressive prune" of the `current-state.md` ▶ Next action callout.** It had
  grown to a **40.5 KB wall** inlining passes 14–17 plus deep band-#1020/#930/#900/mining/BTD6 history that
  duplicated each band's own `planning/reconciliation-pass-*` record. Replaced it with a lean 3.3 KB live
  queue (the eighteenth-pass headline + the next-band startables + the owner-gated list), pointing to the
  per-band records for history. This is the build the band-#1200 pass's Q-0089 idea
  ([`reconcile-pass-tail-trim-actuator`](../ideas/reconcile-pass-tail-trim-actuator-2026-06-20.md)) called for,
  done by hand this pass; the *actuator* to make it deterministic stays a buildable slice.
- Re-homed the band-#1170 + band-#1200 pass records (the prune had been their only inbound link; this record's
  Status header now chains to band-#1200 → band-#1170, restoring reachability).
- Regenerated `dashboard/data/dashboard.json` (cadence freshness).
- **Runtime bugs noticed this pass:** none new (docs-only pass; BUG-0019 #1 stays the open owner-design fork,
  BUG-0011 stays the open Hermes-infra item — both pre-existing).

## 4. The next band (depth to #1260)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** The
creature-game runtime lane alone is multi-PR (PvP user-facing flow in flight → leaderboards → ranked), and
on top of it sit the botsite-React migration, the consistency-linter AI-nav clear-down, procedures→skills
Batch 2, and the Pokétwo/MusicBot mapped features. **Honest caveat (carried, unchanged):** the
*cleanly-ungated self-merge* subset is thinner than the headline count — most of the deepest lanes are
runtime / `needs-hermes-review` (creature PvP cog, AI-nav, CLAUDE.md-editing batches), so an empty
*autonomous* fire should prefer a substantial review-gated lane or promote a fresh idea → plan → build
(Q-0172) over a marginal guard.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Creature-game PvP — user-facing flow** | `needs-hermes-review` | IN FLIGHT as #1230; if it lands, the next slice is below. [plan](creature-game-design-and-sim-2026-06-20.md) §4. |
| A2 | **Creature-game — leaderboards + reuse `game_xp`** | `plan-first` | Reuses the shared game-XP service like fishing/mining; additive, read-mostly. |
| A3 | **Creature-game — result persistence / ranked** | `plan-first` | The PvP v1 records nothing; a later slice adds a results table + ranked. Runtime, `needs-hermes-review`. |
| B1 | **botsite React-SPA migration** | `plan-first` | [plan](botsite-react-spa-migration-plan-2026-06-20.md) — migrate the live bot-site onto the design-system React app. |
| C1 | **Consistency-linter AI-nav PR 1** | `plan-first` | [plan](ai-panel-inplace-navigation-plan-2026-06-19.md); clears the 17 `views/ai/` `edit_in_place` findings, then graduates the rule. Runtime/Q-0086, `needs-hermes-review`. |
| C2 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → `needs-hermes-review`. |
| D1 | **Reaction-roles PR 6 — PIL banner cards** | owner-paced | §4.6d; deliberately deferred, owner-paced. |
| D2 | **Callout-trim actuator** (build the Q-0089 idea) | `ready` | Make the ▶ Next action prune deterministic — `scripts/` helper + a `tests/unit/scripts/` regression (a dispatch run, not a docs-only pass). [idea](../ideas/reconcile-pass-tail-trim-actuator-2026-06-20.md). |
| E1 | **Pokétwo/MusicBot mapped features** | `plan-first` | From the #1180 feature-mapping plan, as the owner greenlights individual rows (music respects the #1185 legal findings). |

Gated/owner-paced (not in the buildable count): reaction-roles web builder (Surface A, control-API write +
security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision `botsite/` +
submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · AI-ticket build (Q-0183, own
session) · Explore-hub PR 2 + the gated layers (Q-0182) · dashboard writes / control-API (security review) ·
fishing follow-ons (Q-0175) · BTD6 floors (exhausted).

## 5. The idea + the previous-pass review + the system improvement

**The Q-0089 idea this pass added:**
[`reconcile-callout-line-budget-guard`](../ideas/reconcile-callout-line-budget-guard-2026-06-21.md) — the ▶
Next action callout bloated to 40.5 KB before *any* pass actually pruned it, because nothing *measured* the
bloat: the standing Q-0102 finding was prose, not a number a checker could enforce. The idea: a tiny warn-only
`check_docs` sub-check (or a `check_current_state_callout.py`) that asserts the live ▶ Next action callout
stays under a **character budget** (e.g. ≤ 6 KB) — turning "this callout is a wall" from a judgment a pass
might skip into a CI signal that *names the regression the moment it crosses the line*, the same way
Recently-shipped is ratcheted at 20. It pairs with the prior pass's *actuator* idea (the trimmer that does
the cut); this is the *guard* that tells you the cut is due.

**⟲ Previous-pass review (Q-0102):** the band-#1200 pass was honest and well-structured — its scorecard
correctly predicted the creature-game lane would dominate the next band (A1 shipped, A2 half-shipped this
band), and it *filed* the callout-trim actuator idea **and** flagged that the callout bloat "should be
promoted to a real slice rather than re-noted each pass." **Where it fell short — and this pass corrected
it:** it took only "a first prune-cut" (prepending its own line) and explicitly **deferred the real prune to
"its own ungated session"** that never came — so the wall grew another pass. That is the exact failure mode
the deferral enables: a cleanup that is *always* one session away is *never* done. **The durable improvement
(initiated, not waited-for):** this pass did the prune **in-band** rather than deferring it, and filed the
*line-budget guard* above so the next agent gets a number, not a vibe. The lesson generalizes: when a pass
identifies a contained docs-cleanup it is *already* qualified to do (it is editing this very file), it should
**do it now**, not route it to a hypothetical future session — the reconciliation pass *is* the docs-cleanup
session.
