# Rebuild Phase A · Stage 2 — the subsystem walk (owner-led)

> **Status:** `plan` — **living, in-progress.** This is the canonical Stage-2 artifact: the
> owner-led, one-subsystem-at-a-time walk of the frozen
> [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
> §1.1 capability corpus, using the
> [Stage-2 readiness review](rebuild-stage2-readiness-review-2026-07-03.md)'s per-row template and
> normalized verdict vocabulary. No prior Stage-2 walk artifact existed before this file (verified
> 2026-07-05 — only the readiness-review *contract* existed under
> `docs/planning/rebuild-stage2*`). **Do not create a competing Stage-2 record** — continue this one.
>
> **Precondition check (2026-07-05):** Prompt B (presentation/verification mechanics,
> `docs/analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md`)
> merged via PR #1691 — the readiness review's blocking precondition is satisfied. Gate-0
> (`docs/analysis/rebuild-discovery/foundations/gate-0/README.md`) explicitly states Stage 2 "runs in
> parallel against the frozen contracts — it does not depend on completing this L0 build." Stage 2 is
> **startable now**, independent of Gate-0 ratification and the substrate-kit D-4 gate.
>
> **Owner-led, decision-capturing, not autonomous.** Per the readiness review §5 rule 1: agents
> pressure-test and record; they do not approve surface choices. Only the primary session thread
> (Lane 0) presents owner questions and finalizes decisions — parallel research fans out, but the
> walk itself is one subsystem/coherent-group at a time, serialized on owner input.

---

## 1. Verdict vocabulary (frozen, per the readiness review + Q-0237(g))

Exactly one primary verdict per row: `keep` · `improve` · `merge` · `redesign` · `drop` · `defer` ·
`re-place` · `add`. A row may carry secondary tags: `blocked-by-gate-0`, `blocked-by-owner`,
`missing-prior-art`, `source-uncertain`, `needs-reconciliation` (cog exists but BUILD-PLAN
disposition looks stale/wrong — a finding, not a blocker).

## 2. Walk order — rationale

Ordered by the frozen BUILD-PLAN §2 build order (L0→L5, itself dependency-topological), with the
Stage-1 global review's **D-1 reorder** applied (welcome moves from L1b to L1c, immediately after
the visual card engine — an engine-class dependency correction, Q-0220). This satisfies the task's
three grounding criteria simultaneously: frozen dependency order, foundation-before-consumer (S-2),
and actual cross-cutting dependencies. **L0 (the kernel/runtime skeleton) is not walked as a Stage-2
owner row** — it is Lane G's territory (already GO-verdicted) and Gate-0's operational build, not a
Discord-facing capability with a product surface; it is tracked in the non-cog queue (§4) for
coverage-completeness only, not for a triage verdict.

The first walked row is **settings** (L1a, position 1): every other subsystem depends on the
settings/config-hub foundation (S-2 foundation-before-consumer), and it is the BUILD-PLAN's own
"generated-config-hub proof" — the frozen build order's own starting point.

## 3. Progress index

State vocabulary: `not-mapped` → `mapped` → `ready-for-owner` → `owner-discussing` → `decided` →
`blocked` → `needs-recheck`.

| # | Layer | BUILD-PLAN row | Lane | Current cog(s) | Research | Owner discussion | Verdict | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | L1a | settings | D | `settings_cog.py` + `settings/` pkg | mapped | **owner-discussing** | — | first row walked this session |
| 2 | L1a | diagnostic | D | `diagnostic_cog.py` + `diagnostic/` pkg (+ `health_maintenance_cog.py`? — needs-recheck) | mapped | not-started | — | verify health_maintenance relationship before walking |
| 3 | L1a | help | D | `help_cog.py` + `help/` pkg | mapped | not-started | — | |
| 4 | L1b | admin | A | `admin_cog.py` + `admin/` pkg | mapped | not-started | — | Lane A full ledger exists (5034-line audit) |
| 5 | L1b | server_management | A | `server_management_cog.py` (+ `setup_cog.py`, `quicksetup_cog.py` — needs-recheck) | mapped | not-started | — | BUILD-PLAN note: "register `setup` as real subsystem" — candidate split, ask owner |
| 6 | L1b | moderation | A | `moderation_cog.py` | mapped | not-started | — | 64.2% fit floor; `ModerationActionSpec` envelope decided (Q-0226) |
| 7 | L1b | logging | D | `logging_cog.py` + `logging/` pkg | mapped | not-started | — | spike exemplar, 97% fit |
| 8 | L1b | automod | A | `automod_cog.py` + `automod/` pkg | mapped | not-started | — | |
| 9 | L1b | security | A | `security_cog.py` + `security/` pkg | mapped | not-started | — | |
| 10 | L1b | cleanup | A | `cleanup_cog.py` + `cleanup/` pkg | mapped | not-started | — | 2 unaudited mutation paths — live bug, jumps queue per collaboration-model |
| 11 | L1b | counters | B | `counters_cog.py` + `counters/` pkg | mapped | not-started | — | re-binned operator band, not economy |
| 12 | L1b | channel | A | `channel_cog.py` | mapped | not-started | — | 17 prefix verbs → small slash set |
| 13 | L1b | role | A | `role_cog.py` + `role/` pkg + `role_grants_cog.py` | mapped | not-started | — | 3-of-8-table teardown gap — live bug |
| 14 | L1b | ticket | A | `ticket_cog.py` | mapped | not-started | — | cleanest audited seam in Lane A |
| 15 | L1b | image_moderation | A | `image_moderation_cog.py` + `image_moderation/` pkg | mapped | not-started | — | off-by-default, fail-open, URL-only privacy posture |
| 16 | L1b | proof_channel | D | `proof_channel_cog.py` + `proof_channel/` pkg | mapped | not-started | — | |
| 17 | L1c | visual card engine (ADD) | — | none (new) | mapped | not-started | — | 5+ consumers (welcome/rank/leaderboard/profile cards) — D-1 |
| 18 | L1c | welcome | A | `welcome_cog.py` | mapped | not-started | — | **re-homed here from L1b per D-1** (card-engine consumer) |
| 19 | L1c | ux_lab | D | `ux_lab_cog.py` | mapped | not-started | — | zero-write gallery |
| 20 | L2 | economy | B | `economy_cog.py` | mapped | not-started | — | `transfer()` ready-but-unwired to `!give/!pay` — live gap |
| 21 | L2 | inventory | B | `inventory_cog.py` | mapped | not-started | — | REDESIGN — merge two item tables |
| 22 | L2 | treasury | B | `treasury_cog.py` | mapped | not-started | — | |
| 23 | L2 | xp | B | `xp_cog.py` + `xp/` pkg | mapped | not-started | — | |
| 24 | L2 | karma | C | `karma_cog.py` + `karma/` pkg | mapped | not-started | — | highest-fit non-hub (87%) |
| 25 | L2 | community (hub) | C | `community_cog.py` | mapped | not-started | — | 100% tier-1 proof |
| 26 | L2 | community_spotlight | C | `community_spotlight_cog.py` | mapped | not-started | — | P-1 event-feed candidate |
| 27 | L2 | leaderboard | C | `leaderboard_cog.py` | mapped | not-started | — | **MERGE into kernel** verdict already frozen |
| 28 | L2 | profile surface (ADD) | — | none (myprofile PR C decided-but-unbuilt, Q-0147) | mapped | not-started | — | |
| 29 | L3 | games (hub) | C | `games_cog.py` | mapped | not-started | — | |
| 30 | L3 | blackjack | C | `blackjack_cog.py` | mapped | not-started | — | spike anchor; free-tournament double-pay live bug |
| 31 | L3 | rps_tournament | C | `rps_tournament_cog.py` | mapped | not-started | — | |
| 32 | L3 | deathmatch | C | `deathmatch_cog.py` | mapped | not-started | — | PvP double-settle live bug |
| 33 | L3 | fishing | B | `fishing_cog.py` | mapped | not-started | — | Q-0175 gates the sell leg |
| 34 | L3 | farm | B | `farm_cog.py` | mapped | not-started | — | 100% declarative once amendments land |
| 35 | L3 | creature | B | `creature_cog.py` + `creature_battle_cog.py` | mapped | not-started | — | |
| 36 | L3 | casino | B | `casino_cog.py` | mapped | not-started | — | honest floor 24%; no records store yet |
| 37 | L3 | counting + chain (merged family) | C | `counting_cog.py` + `chain_cog.py` | mapped | not-started | — | already-merged family per BUILD-PLAN |
| 38 | L3 | four_twenty | B | `four_twenty_cog.py` | mapped | not-started | — | |
| 39 | L3 | giveaways (ADD) | — | none (verified zero giveaway code) | mapped | not-started | — | the one genuine ecosystem gap |
| 40 | L3 | starboard (ADD) | — | `starboard_cog.py` **— needs-reconciliation** | pending workflow | not-started | — | **cog already exists** despite BUILD-PLAN "ADD" label — verify real vs stub |
| 41 | L3 | explore hub + wild encounters (ADD) | — | none (new) | mapped | not-started | — | Q-0182/Q-0186 order decided |
| 42 | L3 | mining | B | `mining_cog.py` | mapped | not-started | — | **ports LAST** — whole-stack acceptance test |
| 43 | L4 | ai (platform) | D | `ai_cog.py` + `ai_review_cog.py` | mapped | not-started | — | REDESIGN into specs |
| 44 | L4 | btd6 | D | `btd6_cog.py`, `btd6_reference_cog.py`, `btd6_events_cog.py`, `btd6_strategy_cog.py`, `btd6_ops_cog.py`, `paragon_cog.py` | pending workflow (split detail) | not-started | — | 6 cogs → 1 BUILD-PLAN row; KnowledgeDomainSpec exemplar |
| 45 | L4 | project_moon | D | `project_moon_cog.py` | mapped | not-started | — | Limbus domain partially shipped |
| 46 | L4 | youtube / shared ingestion (ADD) | — | `media_maintenance_cog.py` **— needs-reconciliation** | pending workflow | not-started | — | **cog already exists** (media retention, #829) despite "ADD" label |
| 47 | L4 | utility | D | `utility_cog.py` | mapped | not-started | — | MERGE pack |
| 48 | L4 | general | D | `general_cog.py` | mapped | not-started | — | MERGE pack |
| 49 | L5 | web dashboard + live editor (ADD/REDESIGN) | — | `botsite/` (not a cog) | mapped | not-started | — | FastAPI/uvicorn, not Flask (corrected) |
| 50 | L5 | boards family (ADD) | — | none (new) | mapped | not-started | — | one tagged-board primitive; likely P-1 2nd instance |
| 51 | L5 | bot-migration assistant (ADD) | — | none (new) | mapped | not-started | — | the anti-MEE6/Carl/Dyno wedge |
| 52 | L5 | Railway / ops control-plane (ADD, owner-gated) | — | `hermes_cog.py`? **— needs-reconciliation** | pending workflow | not-started | — | verify hermes_cog is ops surface, not a bot-product capability |

## 4. Non-cog / platform capability queue (preserved separately per task instructions)

These must also receive a Stage-2 disposition but are not walked as ordinary product cogs:

| Item | What it is | Disposition state | Notes |
|---|---|---|---|
| L0 runtime skeleton | bootstrap, loader, config, bus, lifecycle, tasks, health, DB seam, namespace registry | `handled-via-gate-0` | Lane G already GO-verdicted (preserve 6 primitives field-for-field + build K1 namespace registry). `bootstrap_access_cog.py` is its one cog-visible slice (command-access gate installer) — pure platform wiring, not a product surface; carried here for coverage, no triage verdict needed. |
| `hermes_cog.py` | suspected internal agent-workflow/ops control surface, not a player-facing feature | pending workflow verification | if confirmed ops-only: candidate mapping to the Railway/ops control-plane ADD row, or entirely out of the bot-product corpus (a question for the owner once verified) |
| `setup_cog.py` / `quicksetup_cog.py` | currently under server_management | pending server_management walk | BUILD-PLAN's own note flags "register `setup` as real subsystem" — an explicit candidate to split into its own row; decide during row #5 |

## 5. Bidirectional coverage tracking

- **Coverage A (current → plan):** 58/58 loaded cogs assigned a row or non-cog-queue entry above
  (pending 4 `needs-reconciliation` flags to resolve: starboard, media_maintenance, hermes, and the
  btd6-family split detail). 0 cogs currently unassigned.
- **Coverage B (plan → current):** all 43 shipped BUILD-PLAN rows + 10 ADD rows + L0 listed above.
  0 rows currently missing from this index.
- **Coverage C (commands/hidden functions):** not yet started — begins per-row during each walk.
- **Coverage D (dependency rechecks):** none triggered yet (no `drop`/`defer`/`merge`/`re-place`
  verdicts recorded yet).

---

## 6. Per-subsystem records

Records are appended here as each row reaches a stable owner decision (§6 of the task template).
Rows in `owner-discussing` state show the dossier + questions presented, pending the owner's
answer — not yet a durable decision.

### Row 1 — settings

**Status: owner-discussing.** Dossier + questions presented in-session 2026-07-05; awaiting owner
answers before the durable Stage-2 record (full 13-section template) is written.

