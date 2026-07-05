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
| 1 | L1a | settings | D | `settings_cog.py` + `settings/` pkg | mapped | decided | **improve** | first row walked this session; full record above |
| 2 | L1a | diagnostic | D | `diagnostic_cog.py` + `diagnostic/` pkg + `health_maintenance_cog.py` | mapped (deep dossier done) | **owner-discussing** | — | 52 commands (51 prefix+1 slash), pure admin/owner surface. Found: `!diagnostics` and `!platform` are two overlapping hubs (fragmentation); 4 real mutation surfaces (findings/flags/automation/backfill) live in a nominally read-only subsystem; `docs/ownership.md` had stale "`logs` table" drift, fixed on sight this session. |
| 3 | L1a | help | D | `help_cog.py` + `help/` pkg | mapped | not-started | — | |
| 4 | L1b | admin | A | `admin_cog.py` + `admin/` pkg | mapped | not-started | — | Lane A full ledger exists (5034-line audit) |
| 5 | L1b | server_management | A | `server_management_cog.py` + `setup_cog.py` + `quicksetup_cog.py` | mapped | not-started | — | confirmed structural gap: `setup` has **no `SUBSYSTEMS` registry key at all** today (not just "folded into" server_management — genuinely unregistered); `quicksetup_cog`=primary guided `!setup`, `setup_cog`=advanced `!setupadvanced` wizard + on-join launcher. BUILD-PLAN's own note calls for registering it as a real subsystem — decide the split at this row's walk |
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
| 28 | L2 | profile surface (ADD) | — | **`utility_cog.py:114-146`** (`!myprofile`/`/myprofile`) + `views/profile/profile_view.py` + `views/profile/editor.py` | mapped | not-started | — | ⚠ **CAPSTONE CONTRADICTION** — BUILD-PLAN row says "PR C decided (Q-0147) but unbuilt"; it is in fact fully built, including a self-service editor. See §3.6. |
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
| 40 | L3 | starboard (ADD) | — | `starboard_cog.py` (loaded, `disbot/config.py:90`) + `services/starboard_service.py` | mapped | not-started | — | ⚠ **CAPSTONE CONTRADICTION** — fully working (threshold/emoji/self-star/ignore-channels/panel), not a stub. See §3.6. |
| 41 | L3 | explore hub + wild encounters (ADD) | — | `games_cog.py` + `views/explore/world_hub.py`/`world_card.py` + `services/world_registry.py` (explore-hub half only) | mapped | not-started | — | ⚠ **PARTIAL CAPSTONE CONTRADICTION** — the registry-driven explore-hub router already ships; only "wild encounters" (Pokétwo-style catch loop) is genuinely new. Q-0182/Q-0186 order decided. See §3.6. |
| 42 | L3 | mining | B | `mining_cog.py` | mapped | not-started | — | **ports LAST** — whole-stack acceptance test |
| 43 | L4 | ai (platform) | D | `ai_cog.py` + `ai_review_cog.py` | mapped | not-started | — | REDESIGN into specs |
| 44 | L4 | btd6 | D | `btd6_cog.py` (mother cog: panel+ingestion lifecycle+unified `/btd6` tree), `btd6_reference_cog.py` (static lookups), `btd6_events_cog.py` (live NK data), `btd6_strategy_cog.py` (strategy memory+AI-denial diag), `btd6_ops_cog.py` (ingestion ops), `paragon_cog.py` (Paragon calculator) | mapped | not-started | — | confirmed 6-cog split is purely file-size hygiene (800-LOC cog ceiling), one KnowledgeDomainSpec-exemplar subsystem; legacy per-group cogs are now hidden prefix aliases behind the unified tree |
| 45 | L4 | project_moon | D | `project_moon_cog.py` | mapped | not-started | — | Limbus domain partially shipped |
| 46 | L4 | youtube / shared ingestion (ADD) | — | `media_maintenance_cog.py` + `services/youtube_fetch_service.py`/`video_reference_cache_service.py`/`youtube_context_service.py`/`youtube_diagnostics.py` | mapped | not-started | — | ⚠ **PARTIAL CAPSTONE CONTRADICTION** — YouTube fetch/cache/retention already ships (bespoke, ADR-007 shared-platform, deliberately not AI/BTD6-owned); the genuinely-new part is only the *shared, reusable* IngestionPipeline for btd6/project_moon to also consume. See §3.6. |
| 47 | L4 | utility | D | `utility_cog.py` | mapped | not-started | — | MERGE pack; also hosts `/myprofile` — see row 28 |
| 48 | L4 | general | D | `general_cog.py` | mapped | not-started | — | MERGE pack |
| 49 | L5 | web dashboard + live editor (ADD/REDESIGN) | — | `botsite/app.py` + `dashboard/app.py` (both read-only FastAPI, not a cog) | mapped | not-started | — | ⚠ **PARTIAL CAPSTONE CONTRADICTION** — two read-only dashboards already ship; genuinely new is only the write-capable live editor. See §3.6. |
| 50 | L5 | boards family (ADD) | — | none (new; `hermes_cog.py`'s admin-only dispatch bridge is a **dropped** near-neighbor, not a current implementation of this row) | mapped | not-started | — | one tagged-board primitive; likely P-1 2nd instance. **Owner-decided requirement (2026-07-05, replacing the dropped hermes_cog):** must include an AI-assisted, user-facing (not admin-gated) way for any member to report a bug or suggest an improvement about the bot, landing in this board. Shape (NL-only vs. NL+command) pending — see settings-row question panel. |
| 51 | L5 | bot-migration assistant (ADD) | — | none (new) | mapped | not-started | — | the anti-MEE6/Carl/Dyno wedge |
| 52 | L5 | Railway / ops control-plane (ADD, owner-gated) | — | none — `hermes_cog.py` does **not** map here (confirmed) | mapped | not-started | — | Railway/ops control-plane means drift-checker/deploy-alerts/shadow-clone/backups for the bot's *own hosting*; `hermes_cog.py` is a distinct thing (see non-cog queue) — no current cog implements this row |

## 4. Non-cog / platform capability queue (preserved separately per task instructions)

These must also receive a Stage-2 disposition but are not walked as ordinary product cogs:

| Item | What it is | Disposition state | Notes |
|---|---|---|---|
| L0 runtime skeleton | bootstrap, loader, config, bus, lifecycle, tasks, health, DB seam, namespace registry | `handled-via-gate-0` | Lane G already GO-verdicted (preserve 6 primitives field-for-field + build K1 namespace registry). `bootstrap_access_cog.py` is its one cog-visible slice (command-access gate installer) — pure platform wiring, not a product surface; carried here for coverage, no triage verdict needed. |
| `hermes_cog.py` | **confirmed**: the Discord-side entry point of the Hermes→Claude-Code dispatch bridge (`/bugreport`, `/dispatch` — both admin-gated slash commands that POST a work order to the Claude Code Routine `/fire` endpoint, spinning up an autonomous coding session). Not a guild/player-facing feature at all. | **decided — `drop`** (owner, 2026-07-05) | Does **not** map to the Railway/ops control-plane ADD row (that row is about the bot's own hosting/deploy ops, a different concern) — confirmed out of the bot-capability corpus per `NEW-BOT-BUILD-PLAN.md` §1.3's workflow/substrate carve-out. **Owner ruling:** not needed in the new bot's user-facing surface. Dependency recheck (S-2): zero dependents found (`hermes_cog.py`/`fire_work_order`/`HermesCog` referenced only by itself + the `disbot/config.py` extension list) — no dependent-row fallout. **The underlying goal survives, redirected**: an easy, AI-assisted way for *any* member (not admin-only) to report a bug or suggest an improvement about the bot — this becomes a concrete owner-endorsed requirement on the **boards family** ADD row (row 50), not a standalone row. Removing `hermes_cog.py` from the *current* repo (vs. just excluding it from the new-bot corpus) is a separate implementation action, out of this docs-only session's scope — flagged, not executed. |
| `setup_cog.py` / `quicksetup_cog.py` | **confirmed**: functioning today (`quicksetup_cog`=primary guided `!setup`/`/setup`, `setup_cog`=advanced `!setupadvanced`/`/setup-advanced` wizard + on-join launcher), reachable only via server_management's hub button | pending server_management walk (row 5) | **Confirmed structural gap** (not just "currently under"): `setup` has no `SUBSYSTEMS` registry key at all today. BUILD-PLAN's own note flags "register `setup` as real subsystem" — decide the split at row 5's walk. |

## 3.5 Command-surface ground truth (verified 2026-07-05 — supersedes the frozen 271-row JSON)

Per the readiness review's own warning, `ground-truth/command-surface.json` (271 rows: 224 prefix +
30 slash + 17 group) undercounts grouped command verbs — it is a **static AST scan** that stores one
row per top-level `@commands.group`/`app_commands.command` declaration and never descends into a
group's `.command()` subcommands. Booting the real bot in-process via the parity harness
(`parity/harness/boot.py`) and calling `disbot/core/runtime/command_surface_ledger.build_ledger()` —
the **live, fully-flattened** walk (`bot.walk_commands()` + `bot.tree.walk_commands()`) — gives the
actual current total:

**479 command entries = 406 prefix + 73 slash** (vs. the JSON's 271), confirmed independently by the
`parity/coverage.py` denominators (390/406 prefix, 64/73 slash). Example of the gap:
`btd6_ops_cog.py`'s `!btd6ops` group is **1 row** in the JSON but **7 real entries** live (the group
leaf + 6 subcommands). The live ledger also flags 13 cross-cutting findings today: 12 orphan
cog→subsystem mappings (cogs whose class name isn't a registered `SUBSYSTEMS` key — mostly the
btd6-family sub-cogs, `RoleGrantsCog`, `StarboardCog`, `SetupCog`/`QuickSetupCog`,
`CreatureBattleCog`) and 1 duplicate alias name (`create`).

**Per the Stage-1/readiness-review instruction, all future shared-verb / naming-collision / command
surface work in this walk uses `command_surface_ledger.build_ledger()` as ground truth, not the
frozen JSON.**

## 3.6 Capstone-accuracy contradictions found (rubric class 4 — stale/unanchored claim)

Verified 2026-07-05, source-cited. These are corrections *to the frozen BUILD-PLAN/FINAL-REVIEW
capstone itself* — not new owner decisions — surfaced here so no later reader trusts the stale label.
Each is also flagged on its row above (§3) and will get its full owner discussion when that row is
walked, not now:

1. **`/myprofile` is fully built** (row 28) — `utility_cog.py:114-146` + a read-only card
   (`views/profile/profile_view.py`) + a self-service editor (`views/profile/editor.py`) — but
   `NEW-BOT-BUILD-PLAN.md:82` calls it "decided (Q-0147) but unbuilt." Cleanest capstone miss found.
2. **Starboard ships today** (row 40) — `starboard_cog.py`, fully working (threshold/emoji/
   self-star/ignore-channels/panel) — but listed as `ADD-from-plans` (`NEW-BOT-BUILD-PLAN.md:94`).
3. **YouTube ingestion/caching ships today** (row 46) — bespoke fetch/cache/retention — but listed
   as a from-scratch ADD; the real gap is only the *shared, reusable* ingestion-pipeline
   abstraction btd6/project_moon would also consume.
4. **The "explore hub" half of "explore hub + wild encounters" already ships** (row 41) via
   `games_cog` + `views/explore/world_hub.py` (a registry-driven router into mining/fishing
   worlds); only "wild encounters" (the Pokétwo-style catch loop) is genuinely new.
5. **A read-only web dashboard already ships — twice over** (row 49): `botsite/app.py` (public
   site) and `dashboard/app.py` ("developer dashboard, read-only MVP"). The genuinely-new part of
   that ADD row is the write-capable live editor, not the dashboard's existence.

None of these change any row's eventual verdict by themselves — they change what "done" means for
that row (less net-new build, more "wire the existing thing into the unified manifest/hub"). Also
found, structural (not capstone-accuracy) gaps: **`setup` has no `SUBSYSTEMS` registry key** (row 5)
and **`hermes_cog.py` fits none of the 43+10 rows** (non-cog queue) — both flagged in place above.

## 5. Bidirectional coverage tracking

- **Coverage A (current → plan):** 58/58 loaded cogs assigned a row or non-cog-queue entry above.
  0 cogs currently unassigned. All 4 originally-flagged `needs-reconciliation` cogs resolved this
  round (starboard, media_maintenance, hermes, btd6-family split) — see §3.6.
- **Coverage B (plan → current):** all 43 shipped BUILD-PLAN rows + 9 ADD rows + L0 listed above.
  0 rows currently missing from this index. 5 rows carry a capstone-accuracy contradiction (§3.6).
- **Coverage C (commands/hidden functions):** not yet started at the per-command level — begins
  per-row during each walk. Ground truth for this work is now pinned (§3.5): 479 live commands.
- **Coverage D (dependency rechecks):** 1 triggered — `hermes_cog.py` decided `drop` (owner,
  2026-07-05, out of walk-order sequence). Rechecked: zero dependents found, no fallout. Its
  underlying goal (easy bug/feedback reporting) was redirected onto row 50 (boards family) as a
  named requirement rather than left to evaporate.

---

## 6. Per-subsystem records

Records are appended here as each row reaches a stable owner decision (§6 of the task template).
Rows in `owner-discussing` state show the dossier + questions presented, pending the owner's
answer — not yet a durable decision.

### Row 1 — settings

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `settings` · Layer: L1a · Existing disposition: `KEEP`
- **Stage-2 verdict: `improve`** (owner-decided — tightens the bare capstone `keep`)
- Dependents to recheck: none dropped/merged/re-placed; Q-0119 creates a forward link to row 6
  (moderation)
- Source confidence: `source-confirmed` (live source read + 26 test files + design spec §4)

#### 1. User/job summary
- Primary user: guild administrators / the platform owner (operator-only surface)
- Job-to-be-done: "see and change how this bot behaves in my server without reading docs"
- Embarrassing-to-launch-without: one place to find every setting; a visible audit trail
- Prior art: itself — this is a port, not a new feature
- Competitor benchmark: Dyno/MEE6 web-config dashboards (target: parity, in-Discord, free)

#### 2. Command surface
| Command | Slash | Prefix | Aliases | Shared verb? | Kind | Effect | No-arg default? | Notes |
|---|---|---|---|---|---|---|---|---|
| Settings hub | `/settings` | `!settings` | none | no (unique verb) | both | read/safe-write (opens UI) | yes — opens hub | admin/owner-gated |
| Access explorer | — | `!settings access` | none | no | prefix-only | read | yes | independent of the manager kill-switch |
| Help direct-nav | — | — | — | — | panel-only | read | — | `build_help_menu_view` hook, becomes a declared `PanelRef` |

#### 3. Invocation and routing
- Fuzzy typo eligibility: `auto-run safe` (opening a hub is a safe read)
- NL intent eligibility: yes, candidate ("turn off welcome messages" → jump to that page) — not yet built
- NL orchestration eligibility: yes for compound requests, but rides the general C-2 draft/preview lane, not settings-specific; flag that scalar writes reached via any AI rung still need the Q-0225 confirm-before-act rule applied consistently
- Authority: one `settings.mutate`-class capability per setting (existing `capability_required`, empty = administrator floor) + platform-owner global override (already matches Q-0227 verbatim — no change needed)
- Cooldown: 2/10s/user today — folds into the future C-6 cooldown engine, no change needed now

#### 4. Namespace/collision review
- `settings` is a unique flat verb — stays flat top-level per Q-0224, no collision, K1 reserves it as-is

#### 5. Hub, navigation, presets
- Top-level bucket: Admin (hidden node per Q-0237(c))
- Direct-open: `!settings`/`/settings` already satisfies the navigation contract's direct-open rule (Q-0231)
- Gap found: today's "Back to Hub" is a single fixed jump, not the framework's contextual-stack-aware Back — flagged for the Phase-B nav-engine plan, not owner-blocking
- Preset membership: the Settings hub itself is not excludable by any preset (it's the config surface); per-subsystem page visibility follows that subsystem's own preset membership — flagged as an open point for Stage-3 consolidation

#### 6. Capability triage and exact scope
- **Keep:** three-lane split (scalar/binding/resource), one audited mutation pipeline, generated subsystem pages, 4 diagnostic sub-panels, Command Access panel, Access-policy explorer, tri-state resolve chain
- **Improve:** R-10 (`allowed_values` kernel enforcement at the mutation seam, not just a validator/widget hint); page-actionability (mutate bindings/resources in-place, not view+link-out only); Back/Home stack-awareness
- **Defer:** Q-0119 governance-binding schema home → **routed to row 6 (moderation)**, owner-decided this session; binding-mutation kill-switch parity → rebuild-scoped design note, no current urgency (owner-decided)
- **Add:** none new for settings itself (the feedback-capability idea sits on row 50, not here)
- One-line reason: already the rebuild's best-fit subsystem (93%→96%) — `improve`, not bare `keep`, because 6 concrete named gaps are worth closing rather than silently porting forward unfixed.

#### 7. Concrete outperform targets
| Target type | Target |
|---|---|
| Parity target | Dyno/MEE6 web-config dashboards |
| Match | per-feature toggle, channel/role binding pickers, bounded numeric/enum editing, audit history |
| Beat | in-Discord (no separate site/login), free (no paywalled settings), full visible audit trail, tri-state per-guild/global default resolution |
| Self-explanatory edge | "Needs setup"/"Invalid settings"/"Missing bindings" self-diagnosis panels — no mainstream competitor bot ships this |

#### 8. Required engines/specs/seams
| Engine/spec/seam | Tier | In plan? | New/reused | Owner decision needed? |
|---|---|---|---|---|
| SettingSpec/BindingSpec/ResourceRequirement | T1 | yes (§2.5) | reused | no |
| SettingsMutationPipeline → kernel/workflow scalar lane | T1/T2 | yes (§4.1) | reused | no |
| R-10 `allowed_values` enforcement | T1 rider | yes (ratified) | reused | no |
| PanelSpec/NavigationSpec | T1 | yes (§2.3/§2.4) | reused | no |
| G-10 ModalFormSpec (number/text edit modals) | T2 | yes (ratified) | reused | no |
| C-3 preset/template primitive | T2 | proposed, unbuilt | reused-when-built | no — timing deferred this session |
| C-1 command resolver | T1 engine | proposed (endorsed) | reused-when-built | no |

#### 9. Data, import, lifecycle
- Stores: `guild_settings` (KV), `subsystem_bindings`, resource-requirement tables, `settings_mutation_audit`
- Import mapping: `imported` — verbatim tri-state import (design spec §4.4/§5.2): stored `false`/`true` import as explicit and keep winning forever; only *absent* rows arrive `unset` (the sole population any new `activation` default touches)
- Guild join/leave: no dedicated bootstrap/teardown beyond the `unset` terminus; each declaring subsystem owns its own binding/resource teardown
- Member erasure: n/a — guild-scoped, not member-scoped

#### 10. Verification oracle
- Oracle type: parity golden (a port+improve, not a new feature)
- Existing goldens: ~8,300 lines / 26 test files already cover round-trip edit/reset, every authority path, kill-switch behavior, audit-CHECK alignment — strong oracle to carry forward
- New goldens required: R-10 enforcement (reject an out-of-`allowed_values` write at the pipeline, not just the UI); the AI-projection atomicity fix (once built, see §12)

#### 11. Rubric pass — 10 probes
| # | Class | Result |
|---|---|---|
| 1 | Dependency-order inversion | None — settings correctly sits at L1a, before every consumer |
| 2 | Forgotten capability | None for settings itself (the adjacent forgotten item — hermes_cog's feedback-reporting goal — is resolved onto row 50) |
| 3 | Thin/underspecified step | N/A — unusually well-documented (93-96% fit, deep tests) |
| 4 | Stale/unanchored claim | **Found+fixed**: the 2026-06-12 production-readiness doc's 36/13/11 setting/binding/resource counts are stale vs. today's live 100/17/15 — recorded in-line so no later reader trusts the old figures |
| 5 | Fragmentation/reinvention | **Found**: presets reimplemented ≥7× bot-wide, settings' numeric-presets widget is one instance — tracked as C-3, timing deferred |
| 6 | Under/wrong-generalization | None found |
| 7 | Missing cross-cutting standard | **Found**: R-10 is exactly this class — already ratified as a rider |
| 8 | Verification hole | None — oracle is strong; the 2 live bugs found are correctness gaps, not verification holes (new goldens tracked in §10) |
| 9 | UX/lifecycle-contract gap | **Found**: Back is single-level, not stack-aware — flagged for Phase-B nav engine |
| 10 | Naming/collision risk | None — `settings` is a unique flat verb |

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Owner decision | Q-0119 governance-binding schema home | **Deferred to row 6 (moderation)** — owner-decided 2026-07-05 |
| Live bug | AI-scalar → typed-policy projection is non-transactional (silent drift risk) | **Owner-decided 2026-07-05: queue a contained current-bot bug-fix PR.** Not implemented in this session — this Stage-2 walk is explicitly docs/planning-only and must not edit `disbot/` runtime code; recording it here is the durable "don't lose this" home until a bug-fix session picks it up. |
| Live bug | No operator kill-switch on binding mutation (asymmetric with settings/provisioning) | **Owner-decided 2026-07-05: defer to the rebuild's binding-lane design** — no evidence of live harm |
| Dependency not settled | Preset-widget migration timing to C-3 | Deferred — revisit when C-3 itself is scheduled, no artifact needed now |
| Source uncertainty | Restart-safety of the current `SettingsHubView` not confirmed either way this pass | Flagged for Phase-B verification, not owner-blocking |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: verdict tightens from bare `KEEP` to `KEEP+IMPROVE` with 6 named closure items (R-10, page-actionability, Back/Home stack-awareness, preset-C3-candidacy, AI-projection atomicity, binding kill-switch parity)
- Gate-0 delta: none beyond the already-ratified R-10 rider — no new amendment needed
- Dependencies to recheck: row 6 (moderation) inherits Q-0119; row 50 (boards family) inherits the hermes_cog-replacement feedback requirement (already recorded there)
- Owner ratification needed: none outstanding — verdict, bug-fix priority, and Q-0119 routing were all decided live this session

