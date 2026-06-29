# Admin — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `admin` · **Type:** server-fn · **Family:** platform
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/admin_cog.py` (`!adminmenu`/`/admin`, `!coglist`, server stats, slash-sync,
> Help routing) · `disbot/cogs/admin/cog_manager.py` (Cog Manager — windowed select, owner-gated
> load/unload/reload) · folio `docs/subsystems/health-diagnostics.md` / server-management

> Assessed during the completion-first arc (Q-0209). Admin is the **bot-administration hub**: the
> `!adminmenu`/`/admin` panel that routes to cog management, server stats, slash-sync, and the
> child platform subsystems (server_management, channel, diagnostic, logging, settings, ai), and the
> Cog Manager (`!coglist`) with a **windowed** select (BUG-0017 fix — no silent >25 drop) and
> owner-gated load/unload/reload (protected-cog unload refused, reload allowed). Cog operations are
> **runtime-only** (not persisted; restart recomputes from the filesystem — correct for a dev tool), so
> there is no DB mutation seam to audit. Entry commands are administrator-gated; the dangerous button
> callbacks re-check **owner**. The one honest finding: the panel view relies on the command-level admin
> gate and doesn't re-check admin in `interaction_check` (defense-in-depth; low risk since the panel is
> author-locked and command-gated).

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — cog load/unload/reload (shared idempotent bodies), server stats,
      diagnostics access, slash-sync (diff-gated); cog list with status glyphs (load/syntax/protected).
- [x] **Every best-in-class sub-option** — windowed cog select (paginated), reload-all, protected-cog
      guard, escape-hatch `!cog` prefix; appropriate for a bot-admin tool.
- [x] **Failure modes honest** — load/unload errors surface in embeds/ephemerals; protected-cog unload
      refusal cites the escape hatch.
- [x] **Idempotent** — load/unload/reload settle to the same state; slash-sync skips when no diff.

### B. Reachability & UI
- [x] **A command panel exists** — `!adminmenu`/`/admin` → `_AdminPanelView` (9 destination buttons);
      `!coglist` (+ aliases) → Cog Manager.
- [x] **Reachable every natural way** — commands + `build_help_menu_view` hook + it IS the admin hub
      (child subsystems route back via the back button).
- [N/A] **Integrated into Setup** — admin tooling, not onboarding config.
- [x] **Return navigation** — "↩ Back to Admin" auto-attached to sub-views (rebuilds fresh); windowed
      cog select (◀/▶), no dead-ends.
- [x] **In-place, not spammy** — load/unload/reload re-render the same embed; refresh clears status.

### C. Convenience
- [x] **Bulk + paginated** — "Reload All" button; windowed cog list (no >25 truncation, BUG-0017 fix).
- [x] **Defaults** — per-session actions (no config defaults needed for an admin tool).
- [x] **Clear feedback** — status string appended on each op; glyphs (✅/❌/🟢/🔴/🛡) at a glance.

### D. Authority & safety
- [ ] **Authority re-checked at callback** — ⚠ **partial.** Entry commands are `administrator`-gated and
      the panel is invoker-locked (`BaseView.interaction_check`); the **dangerous** cog load/unload/reload
      buttons re-check **owner** at callback. The panel view itself does not re-check *admin* in
      `interaction_check` (relies on the command gate). Low risk → punch #1.
- [N/A] **All mutations through the audited seam** — cog ops are **runtime-only** (no DB write, not a
      guild mutation); not persisted by design. No audit seam applies.
- [N/A] **Provisioning pipeline** — no resource creation.
- [x] **Reuses governance** — administrator tier + owner floor on the destructive ops; capabilities
      declared (`admin.cog.load/unload/reload`, `admin.server.stats`).

### E. Configuration
- [N/A] **Settings pipeline** — admin has no per-guild config schema (registry metadata only).
- [N/A] **config-input widgets** — n/a.
- [N/A] **Everything configurable that should be** — n/a.

### F. Wiring & discoverability
- [x] **Registry** — key `admin`, `visibility_tier: administrator`, entry `adminmenu`, capabilities
      (cog load/unload/reload + server stats); top-level admin section hosting the platform children.
- [x] **Discoverable in Help** — `build_help_menu_view` hook; commands carry docstrings (note: `!coglist`
      has aliases, `!adminmenu` has none → punch #2).

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_admin_cog_manager.py` (windowing/no->25-drop, shared bodies),
      `test_admin_menu_integration.py` (panel shape, 9 nav buttons, Help hook, back-to-admin),
      `test_admin_slash_sync.py` (owner-only, scope, diff-gating), `test_admin_restart.py`.
- [x] **Authority tests** — owner-gate on load/unload/reload buttons + slash-sync (per-callback);
      protected-cog refusal.
- [N/A] **Mutation-seam tests** — runtime-only ops (no DB seam); the cog-state contract is tested via the
      manager tests.
- [ ] **Live walkthrough recorded** — pending → punch #3.
- [ ] **Owner ✔** — pending → punch #4.

## Punch-list (clear these to certify)
1. **Panel admin re-check (defense-in-depth)** *(offline, minor)* — add `interaction_is_admin` to
   `_AdminPanelView.interaction_check` so the panel doesn't rely solely on the command-level gate.
2. **`!adminmenu` aliases** *(offline, minor)* — add aliases (e.g. `!admin`) for parity with `!coglist`.
3. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot, open the panel, load/unload/reload a
   cog as owner and as non-owner (rejection), reload-all, with screenshots.
4. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/cogs/test_admin_cog_manager.py` · `…/test_admin_menu_integration.py` ·
  `…/test_admin_slash_sync.py` · `…/test_admin_restart.py`
- **Walkthrough:** pending (punch #3)
- **Owner sign-off:** pending (punch #4)

## Verdict
Admin is a **structurally complete** bot-administration hub — windowed cog management (BUG-0017 fix),
server stats, diff-gated slash-sync, and routing to the platform children, with destructive cog ops
**owner-gated at the callback** and protected cogs guarded, plus a strong test suite. It is **not yet
`✔ certified`**: the gaps are one **defense-in-depth panel re-check** (#1, low risk), an alias nicety
(#2), and the live walkthrough/sign-off (#3/#4). Cog ops are runtime-only by design (no audit seam
applies). No dead-end issues found.
