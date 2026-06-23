# Consolidation & Discoverability — ultracode fleet plan

> **Status:** `historical` — ✅ **EXECUTED (2026-06-23).** The ultracode fleet ran: coordinator #1375
> (Phase-0 verify + Phase-2 `edit_in_place`→error graduation), workers U1 AI panels #1376, U2 roles +
> `!temproles` #1377, U3 games hub #1378. The remaining units (U4–U11) were covered by the guards
> (#1370/#1371/#1385) + follow-on PRs (#1382/#1383/#1386/#1390) rather than a second fleet wave — see the
> [audit brief](consolidation-discoverability-audit-brief-2026-06-23.md) status header for the full
> disposition. Kept for provenance (the parallel-run model + the unit roster); not a live to-do.
> Source code + merged PRs win over this doc. **Sector:** S1/S4 (cross-cutting).

## The model in one paragraph

ultracode = one **coordinator** session that spawns up to ~16 **worker** agents, each with a strict
per-unit prompt, checks their work, fixes misses, and merges at the end. That only preserves structure
on a *consolidation* task (a convergence problem) if three things hold: **(1)** the shared pattern every
worker conforms to already exists (Phase 0), **(2)** the work is partitioned into **file-disjoint** units
so two workers never touch one file, and **(3)** machine-checkable **gates** are the reviewer, not human
attention. This plan supplies all three.

## Phase model

| Phase | Who | What | Parallel? |
|---|---|---|---|
| **0 — rails** | coordinator, **serial** | the shared primitives + guards every worker converges on | no |
| **1 — leaves** | **fleet**, parallel | each worker applies the rubric to its own cog's files only | yes |
| **2 — reconcile** | coordinator, serial | verify each PR green on the latest head, merge in order, reconcile `current-state`, graduate `edit_in_place`→error | no |

## Phase 0 status (the rails)

**The machine reviewer is the load-bearing part — most of it already exists:**

- ✅ **Per-command reachability guard (#1370)** — `scripts/check_command_reachability.py` +
  `tests/unit/invariants/test_command_reachability.py`. **CI-enforced ratchet** (a *new* unreachable
  command fails the build), allowlist `architecture_rules/command_reachability_exceptions.yml`. This is
  the key guard — it means a worker **cannot merge an orphaned command** (the general-cog class), so the
  fleet can't reintroduce the fragmentation we're removing.
- ✅ **Shared hub-child discovery primitive (#1371)** — `disbot/views/hub_children.py`
  `discover_hub_children(hub_key)`; the games/community/utility hubs now all delegate to it (one source,
  3 consumers, 68 hub tests green). This is the canonical "which children does my hub surface" seam.
- ✅ **Shared hub-child *button* primitive (#1373 — the "first consolidation", done)** —
  `disbot/views/hub_children.py` `HubChildButton`: the shared open-child-in-place logic (governance
  recheck → `build_help_menu_view` → back-nav → edit), parametrized by `hub_key` + `back_attacher` + an
  optional `fallback_builder`. **Community + Utility** now bind it as thin subclasses (the two
  byte-identical copies removed). **Games** keeps its `handle_select` (extra dropdown-legacy guards + the
  in-place fallback) for now — the shared button already supports its fallback shape via `fallback_builder`,
  so its migration is a **drop-in U3 follow-on**.
- ✅ **Already error-level + failing CI** (from the guardrail inventory): `back_button` ·
  `panel_base_class` · `select_option_truncation` (`scripts/check_consistency.py --mode strict`) ·
  layer/mutation boundaries (`scripts/check_architecture.py --mode strict`) · the audited-write
  invariants (`test_no_direct_*`) · help-homing/roster consistency.
- 🟡 **`edit_in_place`** — warn-only, **36 findings** (18 `views/ai/`, 15 `views/roles/`, 2 casino, 1
  cleanup). This is the fleet's primary *work*: drive it to 0, then graduate the rule to error in Phase 2.
- ⏳ **Settings-orphan guard — Phase 0.5, specced not built (this session's finding).** The live
  `customization_catalogue` discovers panels by **walking the live bot**, so `build_catalogue(None)`
  returns 0/0 in CI — it's blind offline. A CI-safe guard must reimplement panel discovery statically.
  **Approach:** reuse `check_command_reachability._subsystem_discoverable` (already does the AST panel/hook
  detection) to assert *every subsystem that declares settings has a discovery path*
  (settings-without-panel), warn-first with an allowlist. ~80 lines + a ratchet test.
  **⚠ Correction (2026-06-23, verified):** the originally-specced offline source
  `core.runtime.subsystem_schema.all_schemas()` is **also bot-walk-dependent — it returns `{}` offline**
  (schemas register at `cog_load`). Use a **static** "declares settings" source instead: the
  per-subsystem `disbot/utils/settings_keys/<x>.py` files (one per settings domain) and/or AST-scanning
  the `register_schemas` call sites in cog files. Mind that `settings_keys/` names are *domains*, not
  always 1:1 subsystems (`btd6_cache`, `governance`) — map carefully to keep false-positives low. This
  makes Phase 0.5 a genuine (not turn-key) design task. **Build this before the settings/admin fleet
  units** (not a blocker for the AI-panel / roles units, which `edit_in_place` + `back_button` already gate).

**Phase-0 remaining before fan-out:** the settings-orphan guard (0.5, above) **if** the first wave
includes settings work; otherwise the rails are complete for the AI-panel + roles waves now.

## The held set — files NO fleet worker may touch (coordinator/serial only)

These are shared by many units; concurrent edits collide. All homing/registry/settings-catalogue changes
go through Phase 0, so workers touch only cog-local files.

**CRITICAL (never parallel):** `utils/hub_registry.py` · `utils/subsystem_registry.py` ·
`utils/settings_keys/__init__.py` · `services/governance_service.py` · `services/help_projection.py` ·
`services/help_catalogue.py` · `services/customization_catalogue.py` · `views/base.py` ·
`views/navigation.py` · **`views/hub_children.py`** (the new shared primitive).

**HIGH collision (Phase-0 or strict coordination):** `bot1.py` · `config.py` (cog load order —
`bootstrap_access_cog` first) · `services/audit_events.py` · `services/binding_mutation.py` ·
`services/resource_provisioning.py` · `core/runtime/command_access.py` · `core/runtime/guild_lifecycle_*`
· the AI-platform services (`ai_tools.py`, `ai_tool_catalogue.py`, `ai_natural_language_policy.py`,
`ai_instruction_service.py`).

**MEDIUM:** `migrations/` (append-only, numbered — coordinator assigns the next free number; see
`scripts/check_migration_collision.py`). Per-subsystem `services/*_*.py` families are owned by their unit.

## Phase 1 — the file-disjoint unit roster

Each unit owns its cogs' files exclusively (cog file(s) · its `views/<x>/` · its dedicated
`services/<x>_*.py` · its `utils/<x>/` · its `settings_keys/<x>.py` · its tests). Per-cog rubric items 1
(homed), 2 (every command findable), 4 (back), 5 (BaseView), 7 (audited writes) are **already gated** —
the per-unit *work* is items **3 (edit-in-place → 0)**, **6 (settings reachable)**, and local polish.

| Unit | Cogs | Primary work |
|---|---|---|
| **U1 AI platform** | `ai_cog` (+ `views/ai/`) | **18 `edit_in_place`** → 0; finalize the AI setup advisor (generative step on `setup_advisor_review` — Q-0048 gated). Has a plan: [`ai-panel-inplace-navigation-plan`](ai-panel-inplace-navigation-plan-2026-06-19.md). |
| **U2 Roles & access** | `role_cog`, `role_grants_cog` (+ `views/roles/`) | **15 `edit_in_place`** → 0; **fix the `!temproles` gap** (home `role_grants` or surface+allowlist); extract the channel-deployed-component primitive (`channel-deployed-component-menu-primitive` idea). |
| **U3 Games hub** | the 12 minigames (`blackjack`/`rps`/`deathmatch`/`mining`/`counting`/`chain`/`casino`/`creature`/`farm`/`fishing`/`games`) | casino 2 `edit_in_place` → 0; per-game buttonization polish; **migrate the games child-buttons onto a shared `HubChildButton`** (see "first consolidation" below). Subdivide per-game for more parallelism. |
| **U4 BTD6** | `btd6_*`, `paragon_cog` (+ `views/btd6/`) | **fix the `!btd6strat` gap** — add a Strategy child to `BTD6PanelView` (bespoke hand-built panel; mirror its Live-Events/Towers buttons) + allowlist once surfaced. |
| **U5 Economy & inventory** | `economy`, `inventory`, `leaderboard`, `treasury` | settings reachability; verify economy hub renders its children via the primitive. |
| **U6 Community** | `community`, `community_spotlight`, `xp`, `karma`, `welcome`, `counters` | cleanup 1 `edit_in_place`. *(child-buttons → `HubChildButton`: done #1373.)* |
| **U7 Moderation & safety** | `moderation`, `automod`, `image_moderation`, `logging`, `security`, `cleanup`, `counters` | settings reachability; ephemeral→in-place polish. |
| **U8 Admin & diagnostics** | `admin`, `diagnostic`, `server_management`, `channel`, `proof_channel` | verify admin hub renders children; settings reachability. |
| **U9 Settings & UX-lab** | `settings`, `ux_lab` | gated on the Phase-0.5 settings guard. |
| **U10 Setup** | `setup` (+ `views/setup/`) | the wizard walk (every section yields a real op or honest link-only); `setup/launcher.py` BaseView warning. |
| **U11 Utility/foundation** | `utility`, `general`, `four_twenty`, `bootstrap_access`, maintenance cogs | done for general (#1370); *(utility child-button → `HubChildButton`: done #1373);* xp `rank_view.py` → BaseView + card-engine. |

> **First consolidation — DONE (#1373).** Both halves are now shared in `views/hub_children.py`:
> `discover_hub_children` (discovery, #1371) + `HubChildButton` (the forwarding button, #1373).
> **Community + Utility** bind `HubChildButton` as thin subclasses (2 of 3 copies removed). **Games**
> migration is the only remainder — a **drop-in for U3**: subclass `HubChildButton` with
> `back_attacher=attach_back_to_games_button` + `fallback_builder=_build_no_panel_embed`, then drop
> `_GameHubButton`/`handle_select` (its `__none__`/wrong-parent guards are dropdown-legacy — the direct
> buttons never pass them). The U6/U11 "migrate child-buttons onto `HubChildButton`" tasks are already
> done by #1373.

## Rules of engagement (every worker)

1. **Own only your unit's files.** Never touch another unit's files or the **held set** above.
2. **Born-red, stay red.** First commit creates `.sessions/<date>-<slug>.md` with
   `> **Status:** \`in-progress\``. **Leave it red** — the coordinator flips/merges (see protocol). One
   session card per file → no collision.
3. **Green before handoff.** `python3.10 scripts/check_quality.py --full` **and**
   `python3.10 scripts/check_architecture.py --mode strict` must pass. The per-command reachability +
   consistency ratchets are inside that.
4. **One unit = one PR.** Don't widen scope. Never edit `current-state.md`/`active-work.md` (shared).
5. **Migrations:** run `scripts/check_migration_collision.py`; the coordinator assigns the final number.
6. **Flag self-initiated** on the run-report `⚑` line (Q-0172).

## The merge protocol (born-red → coordinator merges all)

- Every worker PR stays **born-red** (the session gate holds it) — no worker self-merges.
- The **coordinator** is the convergence reviewer: it inspects each unit, fixes the misses, then merges.
- **Order:** Phase-0 rails first (already merging via normal PRs); then the disjoint unit PRs in **any
  order** — because they share no files, each merges clean with CI re-validated on the new `main` head.
  The held-set discipline is what guarantees no merge-time conflicts.
- A worker PR is merged only when green **on the latest `main` head** (rebase/re-run if an earlier unit
  changed a shared-but-allowed file — should be none if the partition held).

## Kickoff prompt (paste into ultracode, after Phase 0 is green)

> Read `docs/planning/consolidation-fleet-plan-2026-06-23.md` and the staging brief it links. Confirm
> Phase 0 is green on `main` (per-command reachability + consistency + arch all passing; the
> `hub_children` primitive present). Then launch one worker per unit in the Phase-1 roster, in parallel.
> Each worker owns ONLY its unit's files, follows the Rules of engagement (born-red card, both checks
> green, one PR), and **leaves its PR red**. Start U1 (AI panel) and U2 (roles) — the two largest
> `edit_in_place` clusters — plus the `HubChildButton` consolidation; hold U9 (settings) until the
> Phase-0.5 settings guard lands. Do NOT touch the held set or another unit's files. As coordinator:
> review each red PR, fix misses, then merge it once green on the latest `main` head. After the AI/roles
> units land with `edit_in_place` at 0, graduate that rule to error in `check_consistency.py` (Phase 2).

## Related

- [`consolidation-discoverability-audit-brief-2026-06-23.md`](consolidation-discoverability-audit-brief-2026-06-23.md) (the rubric + findings)
- [`ultracode-fleet-plan-2026-06-19.md`](ultracode-fleet-plan-2026-06-19.md) (the proven fleet format)
- [`ai-panel-inplace-navigation-plan-2026-06-19.md`](ai-panel-inplace-navigation-plan-2026-06-19.md) (U1)
- `scripts/check_command_reachability.py` · `disbot/views/hub_children.py` (the Phase-0 rails)
