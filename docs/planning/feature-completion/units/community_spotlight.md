# Community Spotlight — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `community_spotlight` · **Type:** server-fn · **Family:** community
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/community_spotlight_cog.py` (`!spotlight`/`!activity` + `SpotlightView`/`GamesView`
> + `build_help_menu_view` + `_on_level_up` EventBus handler) · canonical reads `utils/db/xp.py` + rank
> providers · `disbot/views/community/hub.py` (Community-hub child) · folio community

> Assessed during the completion-first arc (Q-0209). Community Spotlight is a **read-only live dashboard**:
> on demand it surfaces top XP leaders, richest members, a level-up feed (EventBus, capped deque) and
> game leaderboards, in an in-place interactive panel. It reads canonical XP/economy providers, performs
> **no writes** (so the D/E mutation items are N/A), and is governed by user-tier visibility (DM-blocked).
> The honest gaps are **configuration depth** (top-N hardcoded to 3, no scheduled auto-post, no
> announcement-channel binding), one **navigation seam** (the back button only appears when reached via
> the hub, not via `!spotlight` directly), and **test coverage breadth** (3 embed/feed tests; button +
> command paths untested).

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise (highlight active/top members)** — `_build_main_embed` (top-3 XP + top-3 richest +
      level-up stream); reads canonical `db.get_guild_xp_totals` + rank providers.
- [ ] **Every best-in-class sub-option** — ⚠ **partial.** Manual trigger ✓; **missing** scheduled
      auto-post, configurable metric/period/top-N (hardcoded 3), announcement-channel override. → punch
      #6/#7.
- [x] **Failure modes honest** — empty providers → "*No activity yet*"; unchunked guild handled; DM
      rejected with a clear message.
- [x] **Idempotent** — read-only; deterministic embeds; level-up feed is an append-only capped deque.

### B. Reachability & UI
- [x] **A command panel exists** — `SpotlightView` (XP / Richest / Games / Refresh) + `GamesView`
      sub-panel; buttons edit in place.
- [x] **Reachable every natural way** — `!spotlight`/`!activity` + `build_help_menu_view` hook +
      Community-hub child (discovered via registry `parent_hub: community`).
- [N/A] **Integrated into Setup** — read-only; nothing to configure at onboarding.
- [ ] **Return navigation** — ⚠ Games→Spotlight back ✓ and back-to-Community attaches via the hub child
      path, but a **direct `!spotlight` invocation has no back button** (only the hub route attaches it).
      → punch #8.
- [x] **In-place, not spammy** — all transitions edit the same message.

### C. Convenience
- [x] **Aliases + on-demand** — `!activity` shorthand; instant refresh.
- [ ] **Defaults / configurability** — ⚠ hardcoded top-3, fixed metrics, no schedule. → punch #6/#7.
- [x] **Clear feedback** — footer "Updated HH:MM UTC"; clear button labels.

### D. Authority & safety
- [N/A] **Authority re-checked at callback** — read-only, user-tier; visibility is re-checked at the hub
      child entry (`HubChildButton`). No mutations to gate.
- [N/A] **All mutations through the audited seam** — no writes.
- [N/A] **Provisioning pipeline** — no resource creation.
- [x] **Reuses governance** — registry `visibility_tier: user`; DM-blocked; capability
      `community_spotlight.dashboard.view` declared.

### E. Configuration
- [N/A] **Settings pipeline** — no SettingSpec; the feature is stateless/read-only (the level-up feed is
      app-scoped, not per-guild config). An announcement-channel binding would be the one config worth
      adding → punch #7.
- [N/A] **config-input widgets** — none.
- [N/A] **Everything configurable that should be** — pending the #6/#7 deepening decision.

### F. Wiring & discoverability
- [x] **Registry** — key `community_spotlight`, `parent_hub: community`, entry `spotlight`, related
      `xp`/`economy`/`leaderboard`; loaded in `config.py` INITIAL_EXTENSIONS.
- [x] **Discoverable in Help** — `build_help_menu_view` hook; auto-discovered as a Community child.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_community_spotlight_cog.py` (3 cases): main embed with unchunked guild,
      main embed uses DB totals, level-up feed caps at the max.
- [N/A] **Authority tests** — read-only (no authority changes); visibility-governance test is a coverage
      gap → punch #2 area.
- [N/A] **Mutation-seam tests** — no mutations.
- [ ] **Live walkthrough recorded** — pending → punch #9 area.
- [ ] **Owner ✔** — pending.

## Punch-list (clear these to certify)
1. **`_build_provider_embed` tests** *(offline, coverage)* — empty/None-provider + top-N rendering.
2. **View-callback tests** *(offline, coverage)* — XP/Richest/Games/Refresh + GamesView back + the
   `!spotlight` DM rejection + `_on_level_up` payload.
3. **Direct-command back button** *(offline, minor)* — attach a return/Help path when reached via
   `!spotlight` (today only the hub route attaches back-to-Community).
4. **Top-N / metric configurability** *(owner, deepening)* — make top-3 + the metric/period configurable.
5. **Scheduled auto-post** *(owner, deepening)* — optional periodic spotlight to a bound channel.
6. **Document the manual-only design** *(owner, minor)* — record whether auto-post is intentionally
   deferred.
7. **Announcement-channel binding** *(owner, deepening)* — a per-guild channel pointer (vs the hardcoded
   `default_channels`).
8. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + `!spotlight` → each sub-panel → back,
   with screenshots.
9. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/cogs/test_community_spotlight_cog.py` (3 cases)
- **Walkthrough:** pending (punch #8)
- **Owner sign-off:** pending (punch #9)

## Verdict
Community Spotlight is a **functionally core-complete read-only dashboard** — top members + level-up feed
+ game leaderboards, reading canonical providers, with honest empty/DM handling, in-place UI, and clean
hub/Help wiring. It is **not yet `✔ certified`**: the gaps are **configuration depth** (top-N / metric /
schedule / announcement-channel — #4/#5/#7), one **back-nav seam** on the direct command (#3), and
**test-coverage breadth** (button/command paths — #1/#2). No safety/audit issues (it is read-only); for a
v1 user-tier dashboard this is acceptable, but the ceiling needs config depth before "done-done."
