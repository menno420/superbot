# Consolidation & Discoverability Audit — staging brief

> **Status:** `plan` — owner-directed staging brief for a **full per-cog consolidation/discoverability
> audit** to be run in a fresh session (2026-06-23). This is **not** a buildable code spec; it is the
> handoff that tells the audit session what's true, what's broken, and how to proceed. Source code +
> merged PRs win over this doc; `docs/current-state.md` owns what is live. **Sector:** S1 — Bot product
> (cross-cutting). **Folios:** [server-management](../subsystems/server-management.md) ·
> [settings-bindings-provisioning](../subsystems/settings-bindings-provisioning.md) ·
> [ai](../subsystems/ai.md).

> **▶ Session 1 SHIPPED (2026-06-23, PR #1370).** Foundation done: the general-cog
> "unfindable" **root cause is found statically** (the Utility hub panel didn't surface its
> `general`/`four_twenty` children — §3.2) and **fixed** (the panel now renders child buttons +
> lists them in the embed, mirroring the Games/Community hubs); the **per-command reachability
> guard** is built (`scripts/check_command_reachability.py` +
> `tests/unit/invariants/test_command_reachability.py`, warn-first ratchet) and emits the **per-cog
> gap list** ([214 commands → 2 genuine gaps; 6 reachable-via-panel commands source-verified +
> allowlisted, incl. a `!cbrecord` one-line fix](../audits/command-reachability-gaps-2026-06-23.md)).
> Sessions 2 (AI panel) and 3 (roles) remain; the 2 gap cogs are tiny per-cog follow-ons.

## 1. Mandate (why now)

The last ~week was heavy net-new feature shipping — farm, karma, casino/poker, treasury, deep fishing,
the visual card engine, reaction-roles, starboard. That breadth was needed. **Now the owner wants to
step back and consolidate.** The product principle this serves is the project's own north-star Pillar 3
([`ideas/competitive-positioning-north-star-2026-06-23.md`](../ideas/competitive-positioning-north-star-2026-06-23.md)):
*"every surface we ship should feel finished, or it drags the whole bot's perceived quality down —
breadth-without-polish is our main self-inflicted risk."*

**The terminal goal of the audit sequence:**

> Every command in the bot is **findable and buttonized**; the setup wizard is improved; the AI advisor
> is finalized; and per-cog + general bot settings are reviewed and made accessible. **No loose ends —
> no forgotten ephemeral panels, no orphaned cogs/commands missing from the help menu, no per-cog
> settings unreachable from a hub.** The bot must be discoverable for a brand-new server owner who does
> **not** already know where everything lives.

**Method (owner-directed):** take **one cog at a time, or a few that connect** (e.g. the games hub
family, the AI panel family, the moderation/safety family), solidify and centralize each, then move on.
Refactor toward shared primitives where the same shape repeats. This is a *solidify-what-we-have* pass,
not a new-feature pass.

## 2. Reconciled product-status findings (code-verified)

A research pass (this chat + a ChatGPT Deep Research report) found the **planning index lagged the live
repo**. These were verified against source this session and are corrected in
[`planning/README.md`](README.md) + [`current-state.md`](../current-state.md):

| Feature | Was labeled | Actually (code-verified) |
|---|---|---|
| **Karma** | "plan-first, 5 gating Qs" | **SHIPPED #1332** — `services/karma_service.py`, `cogs/karma_cog.py`, `utils/db/karma.py`, migration `093_karma.sql`. Only PR 3 (reaction-grant + karma-roles) owner-deferred. Folio: `subsystems/karma.md`. |
| **Starboard** | "▶ buildable, 2 PRs" | **SHIPPED PR1 #1259 + PR2 #1270** — `services/starboard_service.py`, `cogs/starboard_cog.py`, `views/starboard/config_panel.py`, migrations `083`/`084`. |
| **Reaction-roles overhaul** | "▶ buildable" | **SHIPPED PRs 1–6** (#1219/#1220/#1279, Carl-bot-mature) — `services/reaction_role_service.py`, `views/roles/role_menu_builder.py` + `role_menu_view.py`, migrations `078/079/081/089`. Remainder = **web builder Surface A** (owner-paced). |

**Lesson for the audit (and every session):** the `planning/README.md` status column is **not**
authoritative for "is it built?" — only `current-state.md` Recently-shipped + the actual
services/migrations in code are. Apply the repo's own precedence rule (source & merged PRs >
current-state > planning docs) to *status*, not just to the plan list.

**Genuinely-unstarted, by contrast (verified):** the **giveaway system** (no `*giveaway*` file, no
migration) is real and unstarted. The **generative AI-setup** capability is unbuilt (see §3.5).

## 3. Discoverability findings (the core of the audit)

### 3.0 Scale of the surface

**55 cogs** (51 `*_cog.py` + cog packages), **70 registered subsystems**, **6 mother hubs**
(Games · BTD6 · Economy · Community · Utility · Server&Admin) in `utils/hub_registry.py`. The help
system is well-architected at the **subsystem** level (see §3.1) — the gaps are at the **command** and
**panel** level, which is exactly where a new user gets lost.

### 3.1 How help works today (the architecture is sound at subsystem level)

- `cogs/help_cog.py` (HelpCog) + `cogs/help/route.py` (typed `!help <name>` and dropdown resolve to one
  destination) + `cogs/help/panels.py` (`HelpCategoryView` mother-hub dropdown, persistent).
- `services/help_projection.py` is the single projection seam (HLP-2/HLP-3): every render path filters
  through governance + display-state (SHOWN / DISPLAY_HIDDEN / GOVERNANCE_HIDDEN / ROUTED_OFF /
  COMMAND_LOCKED / UNAVAILABLE / ORPHANED_OVERRIDE).
- `utils/subsystem_registry.py` (70 subsystems, each with `parent_hub`, `visibility_tier`,
  `entry_points`) + `utils/hub_registry.py` (the 6 hubs) drive homing. `validate_registry()` runs at
  boot (unique entry-points, valid parent_hub, no two-hop hubs).
- PR #1294 removed the legacy "All Commands / Advanced" fallback; PR #1297 added a help-reachability
  guard. **Audit TODO — RESOLVED 2026-06-23 (code-verified):** the guard is **subsystem-level only,
  not per-command**. It lives as the invariant test **`tests/unit/invariants/test_help_reachability.py`**
  (which delegates to `tools/sim/help_menu_grouping_sim.py::check_reachability`) plus the sibling
  **`tests/unit/invariants/test_discoverability.py`** (every subsystem must have a discovery path:
  `build_help_menu_view` hook / `KNOWN_PANEL_COMMANDS` entry / `.+menu` entry-point / `internal`). Both
  assert **subsystem** homing — no orphan, ≤3 clicks, no dropdown overflow. **Neither checks per-command
  reachability**, so **rubric item 2 (§4) is currently UNGUARDED** — making it a CI guard is the
  "strongest possible outcome" the audit can still pursue (§6/§8), but it is a genuinely new, non-trivial
  check (mapping each registered command → whether its subsystem's help menu actually surfaces it), so
  scope it as its own slice, not a drive-by.

### 3.2 The real gap: command-level findability + buttonization (the owner's actual point)

The help tree homes **subsystems** under hubs. It does **not** guarantee every **command** is
individually findable or has a button. The owner's report — *"the general cog is completely unfindable
from the help menu"* — is best read as a **command-level** complaint, and it generalizes:

- **`general_cog.py` (class `General`)** defines **8 commands**: `generalmenu`, `fact`, `joke`, `quote`,
  `trivia`, `motivate`, `eightball`, `greet`. **Static registration is clean** — `general` subsystem has
  `parent_hub: "utility"`, `visibility_tier: "user"`, `visibility_mode: "normal"`, a
  `build_help_menu_view` hook, and is a `primary_child` of the Utility hub. So at the *subsystem* level a
  static analysis says "findable."
- **But the owner experiences it as unfindable** — and the owner's lived experience is ground truth over
  static analysis (CLAUDE.md: a green check that contradicts visible evidence is a bug in the check).
  **Code-verified 2026-06-23 narrowing the cause:** `GeneralMenuView` (in `general_cog.py`) **already
  buttonizes all 8 commands** (`fact_btn`/`joke_btn`/`quote_btn`/`trivia_btn`/`motivate_btn`/
  `eightball_btn`/`greet_btn`/`overview_btn`), and `general` is a Utility `primary_child` with a
  `build_help_menu_view` hook — so once you *reach* the general menu, the commands ARE buttoned. That
  **rules out cause (a)** (the buttons exist) and points the live repro at **(b) the path to the menu**
  (Utility is two taps deep / the individual `!joke`,`!fact` aren't listed in the *help-tree text* before
  you open the panel) or **(c) a runtime governance/routing default**.
  **ROOT CAUSE FOUND + FIXED 2026-06-23 (Session 1, PR #1370) — it was (b), structural.** The Utility
  hub panel (`_UtilityPanelView` in `cogs/utility_cog.py`) is a **hybrid** surface — a functional cog
  (server-info/poll/remind/…) *and* the parent hub of `general`/`four_twenty` — but its hand-built panel
  rendered **only its own action buttons and never surfaced its child subsystems**. Unlike the Games
  (`views/games/hub.py`) and Community (`views/community/hub.py`) hubs, which discover children from
  `SUBSYSTEMS` (`parent_hub == …`) and render forwarding buttons, Utility surfaced nothing — so the
  click-path dead-ended (`!help` → Utility → 6 utility buttons, **no General**) and a new user could
  never reach the General panel or see `!joke`/`!fact` exist. **Cause (c) ruled out:** `general` is
  `visibility_tier: user` / `visibility_mode: normal`, never default-hidden. **Fix:** the Utility panel
  now renders a forwarding button per child (`discover_utility_children()` + `_UtilityChildButton`,
  row 3, click-time governance recheck + Back-to-Utility) **and** lists the children in its embed —
  guarded by `tests/unit/cogs/test_utility_hub_children.py`. The owner's live screenshot is still
  welcome as confirmation but is **no longer needed to diagnose**.
- **Generalize it:** for *every* cog, the audit's bar is **every user-facing command is reachable from
  the help tree AND has a button affordance**, not merely "the cog's menu entry exists." `general` is the
  exemplar; the same check applies to all 55 cogs.

### 3.3 Ephemeral-panel / edit-in-place inconsistency (forgotten panels)

`scripts/check_consistency.py` reports **36 `edit_in_place` warnings across 18 files** — panel callbacks
that send a *new ephemeral message* instead of editing the panel in place (the "forgotten ephemeral
panel" class the owner named). Breakdown:

- `views/ai/` — **18** findings (the AI panel family; this is also why the AI-panel-in-place-navigation
  plan exists and blocks graduating the `edit_in_place` rule to error).
- `views/roles/` — **15** findings (reaction-role builder/manager panels).
- `views/casino/` — **2**; `views/cleanup/` — **1**.

The other three consistency rules — `back_button`, `panel_base_class`, `select_option_truncation` — are
**graduated to error** (clean). So the one open structural-consistency debt is `edit_in_place`, and it is
**concentrated in two families (AI + roles)** — ideal first audit targets.

### 3.4 Settings accessibility

`services/customization_catalogue.py::actionable_settings_groups()` live-composes the settings hub
(`views/settings/hub.py`, `!settings`) from the registry + schema declarations (a group is included if
non-internal AND has ≥1 actionable surface: editable scalar, binding, resource, or a domain panel).
**~30–40 groups** surface depending on declarations. The catalogue already computes two orphan signals
the audit should mine:

- **`settings_without_panel`** — subsystems with settings but no panel/hook → unreachable config.
- **`panels_without_settings`** — panels with no settings → actionability gaps.

**Audit TODO:** run these and drive both lists to zero (or explicit exemption) — that *is* the
"every cog's settings reachable from a hub" goal, made checkable. **Code-verified 2026-06-23:**
`build_catalogue(None).findings` already reports **`settings_without_panel == ()` and
`panels_without_settings == ()`** (both empty) in the static build — so this sub-goal is **already at
zero**. The audit still needs a *live-bot* build to exercise the `bot`-dependent signals
(`subsystems_missing_help_hook`, `undiscoverable_surfaces`), which the no-bot static build skips.

**SHIPPED 2026-06-23 — the static settings-reachability guard** (the settings analog of the #1370
command guard): `scripts/check_settings_reachability.py` + `tests/unit/invariants/test_settings_reachability.py`
assert every subsystem that declares a `SubsystemSchema` is non-internal (so it surfaces in `!settings`)
and that every `*.configure`/`*.settings.*`-capability subsystem is either schema'd or explicitly
allowlisted (`architecture_rules/settings_reachability_exceptions.yml`). Result: **19 reachable · 3 exempt
· 0 GAP** — settings are structurally centralized, and now *un-regressably* so. Finding + exemption
ledger: [`audits/settings-reachability-2026-06-23.md`](../audits/settings-reachability-2026-06-23.md).
The *live-bot* signal verification above remains the owner's (it needs a running bot).

### 3.5 Setup wizard + AI advisor (two named finalize targets)

- **Setup wizard** (`cogs/setup/`, `views/setup/sections/`, `services/setup_session.py`,
  `SetupOperation` drafts → Final Review): the owner wants it improved. Known historical finding
  (`cog-improvement-audit`): "half its steps do nothing." The audit should walk every section, confirm
  each produces a real draft op or is honestly a link-only step, and tighten the new-owner flow.
- **AI advisor — finalize:** a **read-only** advisor seam exists
  (`services/setup_advisor_review.py` — "Ask AI to review this setup," advisory text only, deterministic
  default) and a **link-only** `views/setup/sections/ai_setup.py`. The **generative** capability the
  north-star names as the headline wedge — *"describe your server → AI proposes channels/roles/automod →
  staged as `SetupOperation` drafts → apply"* — does **not** exist yet. Finalizing the advisor means
  building that generative step **on the existing advisor + SetupOperation + Final-Review seams** (a
  smaller lift than from scratch). Gated by the AI write-capability rule (Q-0048) — needs its own plan +
  per-exposure decision before any mutation.

### 3.6 Visual consistency (cheap polish wins)

The new themeable card engine (`utils/card_render.py`, #1349) is live but most surfaces are still plain
embeds. The XP **rank card** (`views/xp/rank_view.py`) imports no `card_render`/PIL → still embed-based.
Migrating rank/profile/leaderboard cards onto the engine (card-engine roadmap H2) is a low-risk,
high-visibility consolidation win that makes already-free features (e.g. the MEE6-style leveling +
role-reward thresholds already shipped via migration `056`) also *look* best-in-class.

## 4. The per-cog audit checklist (the reusable rubric)

For each cog (or connected group), the audit confirms — and fixes — all of:

1. **Help-homed:** the subsystem is registered with a correct `parent_hub` and appears in the help tree.
2. **Every command findable:** each user-facing command is reachable from help (not just the menu entry).
3. **Buttonized:** every distinct action has a button/affordance; navigation edits **in place** (no
   stray ephemeral follow-ups → zero `edit_in_place` findings for the cog's views).
4. **Back affordance:** every panel can navigate back (the `back_button` rule, already error-level).
5. **BaseView/HubView:** views extend the sanctioned base (the `panel_base_class` rule, already error).
6. **Settings reachable:** the cog's config is reachable from the `!settings` hub — it appears in
   `actionable_settings_groups()` and is in neither `settings_without_panel` nor `panels_without_settings`.
7. **Audited mutations:** writes go through the domain `*_mutation`/`*_workflow` service with
   `emit_audit_action` (architecture rule — many cogs already comply; confirm the new ones do).
8. **Centralized, no duplication:** if the cog re-implements a shape another cog has (score/leaderboard,
   channel-deployed persistent panel, render), note it for primitive convergence (§5).

## 5. Convergence / shared-primitive flags (refactor targets)

The audit should consolidate these recurring shapes rather than leave parallel copies:

- **Audited per-user score subsystem** — economy / game-XP / karma repeat the identical six-piece shape;
  capture `audited-score-subsystem-scaffold` exists. Karma/leaderboard/treasury are the convergence set.
- **Channel-deployed persistent component menu** — role menus, starboard, (future) giveaways/polls share
  "post in channel → persist message_id → re-attach on boot → teardown"; capture
  `channel-deployed-component-menu-primitive` exists. Extract at consumer #1.
- **Visual card engine** — one `Theme` + `CardCanvas`; migrate the per-feature renderers (rank, mining,
  welcome, profile) onto it (H2).
- **Settings/panel registration** — `actionable_settings_groups()` + `customization_catalogue` are the
  one place a cog declares its config surface; new cogs must register there, not invent a side panel.

## 6. Existing tooling the audit leverages (don't rebuild these)

- `scripts/check_consistency.py` — `edit_in_place` (36 findings) · `back_button` · `panel_base_class` ·
  `select_option_truncation`. The audit's per-cog rubric items 3/4/5 are already machine-checked here.
- `validate_registry()` (boot) — homing/entry-point integrity.
- `actionable_settings_groups()` + `customization_catalogue` findings — settings reachability (rubric 6).
- `scripts/check_architecture.py` — mutation/layer boundaries (rubric 7).
- `scripts/command_surface_dump.py` + `docs/audits/untested-surface-checklist.md` — the command inventory.
- `scripts/new_subsystem.py` — the scaffold any genuinely-new homing should go through.
- PR #1297's help-reachability guard — confirm scope, then extend it to per-command if it's
  subsystem-only (that would make rubric item 2 a CI guard, the strongest possible outcome).

## 7. Suggested first targets (connected groups, highest debt first)

1. **AI panel family** (`views/ai/`, 18 `edit_in_place` findings) — already has a plan
   (`ai-panel-inplace-navigation-plan-2026-06-19`); doing it clears the largest consistency-debt cluster
   *and* unblocks graduating the `edit_in_place` rule to error. Pair with the AI-advisor finalize (§3.5).
2. **Roles family** (`views/roles/`, 15 `edit_in_place` findings) — reaction-roles shipped fast; this is
   the polish/consolidation tail, and it feeds the channel-deployed-component primitive (§5).
3. **General / Utility cog** (§3.2) — reproduce the "unfindable" report live, fix command-level
   findability + buttonization, and codify the fix as the rubric exemplar for all other cogs.
4. **Settings hub sweep** (§3.4) — drive `settings_without_panel` / `panels_without_settings` to zero.
5. **Setup wizard walk** (§3.5) — every section produces a real op or is honest link-only.

## 8. Open questions to resolve live / with the owner

- **General-cog repro — RESOLVED 2026-06-23 (Session 1):** the Utility hub panel didn't surface its
  `general` child (structural cause (b), found statically — see §3.2), now fixed (PR #1370). An owner
  screenshot of `!help` → Utility is still welcome as live confirmation but isn't needed to diagnose.
- **#1297 scope — RESOLVED 2026-06-23:** subsystem-homing only (see §3.1). Rubric item 2 (per-command
  reachability) is **not** guarded; making it one is a standalone slice, not a drive-by.
- **AI-advisor generative step:** confirm the owner wants the "describe-your-server → staged ops"
  capability (Pillar 2 wedge) and route it through the Q-0048 per-exposure decision before building.
- **Casino vs. gambling headwind:** the north-star flags Discord's 2026 teen-safety/age-gating push at
  gambling mechanics; casino/poker shipped the same week. A product-coherence call for the owner (not a
  blocker for this audit, but worth surfacing).

## Appendix A — Session 1 kickoff prompt (paste-ready)

> **Session order vs. §7:** §7 ranks the targets by *consistency debt* (AI panel highest). This appendix
> sets the *owner-prioritized session order* — **findability foundation first**, because it is the
> owner's stated #1 goal *and* it produces the rubric + CI guard that make every later per-cog session
> mechanical. AI panel + roles become Sessions 2 and 3.

Paste the block below into a fresh session to start the audit cleanly from the repo:

---

**Target: Help discoverability foundation — command-level findability + the General/Utility exemplar + a
per-command reachability guard.**

Read first: **this brief** (your mandate, the per-cog rubric §4, the resolved findings §3). Then
`.claude/CLAUDE.md` → `docs/current-state.md` → `docs/current-state/S1-bot.md`.

**Context (already code-verified — don't re-derive):** the help tree homes *subsystems* well
(`cogs/help/`, `services/help_projection.py`, `utils/subsystem_registry.py`, `utils/hub_registry.py`);
the #1297 guard is **subsystem-level only** (`tests/unit/invariants/test_help_reachability.py` +
`test_discoverability.py` — see §3.1). `GeneralMenuView` in `general_cog.py` **already buttonizes all 8
general commands** (§3.2). So the gap is **command-level discoverability**, not missing buttons.

**Do, in order:**

1. **Reproduce the general-cog report (static — no live guild here).** Trace the exact render path
   `!help` → `HelpCategoryView` → Utility hub → General. Determine why a new user can't find
   `!joke`/`!fact`/etc.: **(b)** is Utility surfaced clearly in the top dropdown, and are individual
   commands shown in the help-tree *text* before the panel is opened? **(c)** is there a routing /
   governance default hiding Utility or `general`? Write the root cause with file:line evidence, and
   **flag explicitly the one thing that needs the owner's live screenshot to confirm** (§8).
2. **Fix the deterministic part of that root cause** — e.g. surface individual commands in the subsystem
   help text, raise Utility's discoverability, or correct a wrong routing default — **through the existing
   `help_projection` seam**, no new parallel system. One contained change.
3. **Build the per-command reachability guard** (rubric item 2; the §6/§8 "strongest outcome"): extend the
   invariants so every registered user-facing command resolves to *either* a help-tree listing *or* a
   buttonized panel action — `internal`/owner-tier exempt via allowlist, **warn-first**. Model it on
   `check_consistency.py` house style + the existing `test_discoverability.py`. This is what makes "every
   command findable" un-regressable and the rest of the audit mechanical.
4. **Run it across all 55 cogs**, record the per-cog gap list (append to this brief or a sibling ledger),
   and note which cogs are clean vs. need a follow-on session.

**Acceptance:** general-cog root cause documented + the deterministic part fixed; the per-command guard
exists (warn-first) and emits the full per-cog gap list; `python3.10 scripts/check_quality.py --full` +
`python3.10 scripts/check_architecture.py --mode strict` green. **Scope discipline:** this is the
*foundation* session — do **not** also refactor the AI/roles panels (Sessions 2/3). Born-red session card
first, claim the lane, open the PR ready, auto-merge on green.

**Owner live-confirm needed:** one screenshot of `!help` → Utility (or wherever you land) to confirm the
general-cog repro.

---

**Then (each a standalone session, per "one cog / connected group at a time"):**

- **Session 2 — AI panel family** (`views/ai/`, 18 `edit_in_place` findings) + finalize the AI setup
  advisor (the generative "describe-your-server → staged `SetupOperation` drafts" step on the existing
  `setup_advisor_review` seam, §3.5). Largest consistency-debt cluster; has a plan
  ([`ai-panel-inplace-navigation-plan-2026-06-19`](ai-panel-inplace-navigation-plan-2026-06-19.md)); the
  advisor's generative write is gated by Q-0048 (its own per-exposure decision first).
- **Session 3 — Roles family** (`views/roles/`, 15 `edit_in_place` findings) + extract the
  channel-deployed-component primitive (§5).

## Related

- [`ideas/competitive-positioning-north-star-2026-06-23.md`](../ideas/competitive-positioning-north-star-2026-06-23.md)
- [`ideas/visual-card-engine-vision-2026-06-23.md`](../ideas/visual-card-engine-vision-2026-06-23.md)
- [`planning/ai-panel-inplace-navigation-plan-2026-06-19.md`](ai-panel-inplace-navigation-plan-2026-06-19.md)
- [`planning/repo-consistency-linter-plan-2026-06-17.md`](repo-consistency-linter-plan-2026-06-17.md)
- [`subsystems/settings-bindings-provisioning.md`](../subsystems/settings-bindings-provisioning.md)
