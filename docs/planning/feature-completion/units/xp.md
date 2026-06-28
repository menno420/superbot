# XP & levels — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `xp` · **Type:** server-fn · **Family:** progression
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/xp_cog.py` (`!rank` · `!xpmenu` · admin `!givexp`/`!resetxp`/`!xpconfig` + Help
> hook) · `disbot/cogs/xp/listener.py` (message XP + level-up + threshold-role grants) ·
> `disbot/cogs/xp/stage.py` · `disbot/views/xp/` (`main_panel.py` `_XpHubView` · `config_panel.py` ·
> `modals.py`) · `disbot/services/xp_service.py` (audited XP seam) · `disbot/utils/db/xp.py` (curve +
> primitives) · `disbot/utils/rank_render.py` (H3 rank card) · `disbot/cogs/xp/schemas.py` ·
> `disbot/utils/settings_keys/xp.py` · setup: `disbot/views/setup/sections/roles.py`

> Assessed during the completion-first arc (Q-0209). XP is **functionally solid**: message XP with
> per-user cooldown, a quintic level curve, `!rank` with a themed H3 image card, level-up role rewards
> (XP-level + time-in-server, with a stacking/single-role toggle), level-up announcements, admin
> give/reset, and a persistent `!xpmenu` hub. **During this assessment a real audit gap was found and
> fixed at the root (BUG-0029):** the level-up role grants used a *direct* `member.add_roles`/
> `remove_roles` call that emitted **no audit event** — they now route through the audited
> `role_automation.apply` seam (audit + shared hierarchy preflight), pinned by a new AST invariant. The
> remaining gaps are **best-in-class breadth** (no no-XP channels, no per-channel/role XP multipliers, no
> voice XP, hardcoded curve) — feature scope, not defects.

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — message XP (15–25) with a configurable per-user cooldown
      (`listener.py`, `check_cooldown`), quintic level curve `5·L²+50·L+100` (`utils/db/xp.py`),
      `!rank` (stat views XP/coins/both + other providers), leaderboard (the separate Leaderboard unit),
      level-up role rewards (XP-level + time-in-server) with a stacking/single-role toggle, level-up
      announcements to a bound channel.
- [ ] **Every best-in-class sub-option exists** — ❌ **partial.** **Missing vs MEE6/Arcane:** no-XP
      channels · no-XP roles for *gain* (the exemption service only exempts role *grants*) ·
      per-channel/role XP multipliers · voice XP · admin-tunable level curve · mass-reset · rank-card
      style choice (the `rank_embed_style` schema field is unused). → punch-list #2.
- [x] **Failure modes honest** — cooldown is stateless/idempotent (re-checks `last_xp` each message);
      role-grant failures now classified by `role_automation` (perm/hierarchy preempted once per batch)
      instead of a bare per-call catch; the whole role-grant block is wrapped fail-safe.
- [x] **Idempotent** — re-earning a held role is a no-op; `xp_service` event subscribers are replay-safe.

### B. Reachability & UI — "the most convenient way"
- [x] **A command panel exists** — `_XpHubView` (`!xpmenu`): renders the H3 rank image card, stat-switch
      buttons (Both/XP/Coins), and admin Configure/Give/Reset buttons; degrades to an embed when Pillow
      is absent (`views/xp/main_panel.py`).
- [x] **Reachable every natural way** — `!xpmenu` + `!rank` entry points + Help hook
      (`build_help_menu_view`, which stashes the rank card for the help-nav attachment seam) +
      Community-hub child (`parent_hub: community`).
- [x] **Integrated into the Setup wizard** — the "Auto roles (time & XP)" section
      (`views/setup/sections/roles.py`) stages both time and XP role tiers; the Essential Setup "reward
      active members" step sets XP rate + level/time role rewards (#1434).
- [x] **Return navigation** — the hub→Config panel has a Back button; the `!rank` stat-switch is an
      in-place ephemeral toggle; no dead-ends.
- [x] **In-place, not spammy** — `!xpmenu` persists; `!rank` toggles in place; config modals edit in
      place.

### C. Convenience
- [x] **Admin XP ops** — `!givexp`/`!resetxp` commands + hub Give/Reset modals (member picker + a
      typed "CONFIRM" guard on reset), routed through `xp_service.award`/`reset` (audited).
- [x] **Sensible defaults** — XP 15–25, cooldown 60s (preset picker 0/15/30/60/120/300), in-place
      announcement channel by default.
- [x] **Clear feedback** — the rank image card (900px, stat grid + level progress bar, H3 engine
      parity with profile/leaderboard); admin actions confirm.

### D. Authority & safety
- [x] **Authority re-checked at callback** — admin commands `has_permissions(administrator=True)`; the
      hub's Configure/Give/Reset buttons re-check `guild_permissions.administrator` at callback entry.
- [x] **All mutations through audited seams** — XP grants/resets via `xp_service` (single authority;
      emits `EVT_XP_AWARDED`/`EVT_LEVEL_UP`/`EVT_XP_RESET`; reset fires `audit.action_recorded`), pinned
      by INV-G (`test_inv_g_xp_service.py`). **Level-up role grants now route through the audited
      `role_automation.apply` seam (BUG-0029 fix, this PR)** — `audit.action_recorded` per role change +
      shared hierarchy preflight, replacing the prior direct `member.add_roles`; pinned by
      `test_no_direct_xp_role_mutations.py`.
- [x] **Settings/binding writes audited** — XP range/cooldown via `SettingsMutationPipeline`; the
      announce channel via `BindingMutationPipeline`.
- [x] **Reuses governance** — capability floor (`xp.*`); exemption service for no-grant roles.

### E. Configuration
- [x] **Settings route through the pipeline** — `XP_SETTINGS` (xp_min/xp_max/xp_cooldown) +
      `XP_BINDINGS` (announce_channel) via `SubsystemSchema`, registered at cog load (`schemas.py`).
- [x] **`settings_keys` constants** — `utils/settings_keys/xp.py` (modals write through the pipeline,
      not raw KV).
- [x] **Typed widgets / config-input-standard** — range modal (min/max with max≥min validation),
      cooldown (free-form + preset hint), optional channel id.
- [ ] **Every option configurable** — ⚠️ the level **curve** is hardcoded (no admin override) and the
      `rank_embed_style` preference is defined but unwired. → punch-list #2.

### F. Wiring & discoverability
- [x] **Registry** — key `xp`, `category: progression`, `visibility_tier: user`,
      `entry_points: [xpmenu, rank]`, `parent_hub: community`, related `[role]`, capabilities
      `xp.rank.view`/`xp.leaderboard.view`/`xp.settings.configure` (`subsystem_registry.py`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook (with the rank card via `help_nav_card`).
- [x] **Homed in `ownership.md`** — `services/xp_service.py` owns XP mutations (INV-G); role grants now
      homed under `role_automation`.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_xp_service.py` (event emission, reset audit), `test_xp_helpers_rank.py`
      (rank fetch-once, card attach, Pillow fallback, off-board member), `test_rank_render.py` (card
      geometry), `test_xp_hub_panel.py`, `test_xp_cog_admin_routes.py`, `test_xp_cog_rank_provider.py`,
      `test_xp_participation_gate.py`, `test_xp_listener_roles.py`.
- [x] **Authority/seam tests** — INV-G (`test_inv_g_xp_service.py`) + the **new**
      `test_no_direct_xp_role_mutations.py` (role grants route through `role_automation`); modal
      pipeline tests.
- [x] **Mutation-seam tests** — XP via `xp_service` (audited); role grants via `role_automation` (audit
      asserted in `test_xp_listener_roles.py`).
- [ ] **Live walkthrough recorded** — pending. → punch-list #3.
- [ ] **Owner ✔** — pending. → punch-list #4.

## Punch-list (clear these to certify)

1. ~~**Level-role grants bypass the audited seam**~~ — ✅ **FIXED 2026-06-28 (BUG-0029, this PR):**
   `_apply_xp_threshold_roles` now routes through `role_automation.apply` (audit + hierarchy preflight),
   guarded by `test_no_direct_xp_role_mutations.py`.
2. **Best-in-class breadth (rubric A/E)** *(owner-paced, deepening)* — no-XP channels · no-XP roles for
   *gain* · per-channel/role XP multipliers · voice XP · admin-tunable level curve · mass-reset ·
   wire the `rank_embed_style` card-style choice.
3. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (`!xpmenu`
   card → chat to level up → see announcement + role reward → admin give/reset → setup reward step),
   with screenshots; include confirming the role-reward grant now lands on the audit channel.
4. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_xp_service.py` · `…/test_xp_helpers_rank.py` ·
  `tests/unit/utils/test_rank_render.py` · `tests/unit/views/xp/test_xp_hub_panel.py` ·
  `tests/unit/cogs/test_xp_listener_roles.py` · `tests/unit/invariants/test_inv_g_xp_service.py` ·
  `tests/unit/invariants/test_no_direct_xp_role_mutations.py`
- **Walkthrough:** pending (punch-list #3)
- **Owner sign-off:** pending (punch-list #4)

## Verdict
XP is **functionally solid and now fully audited** — message XP, a quintic curve, an H3 rank card,
level-up role rewards with a stacking toggle, admin give/reset, and a persistent hub. This assessment
**closed a real audit gap at the root (BUG-0029)**: level-up role grants now go through the audited
`role_automation` seam. It is **not yet `✔ certified`**: the remaining gaps are **best-in-class breadth**
(no-XP channels, XP multipliers, voice XP, tunable curve — #2) plus the owner walkthrough/sign-off
(#3/#4). No remaining safety/audit/dead-end issues.
