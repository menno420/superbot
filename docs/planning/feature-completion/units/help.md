# Help — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `help` · **Type:** server-fn · **Family:** platform
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/help_cog.py` (`!help`/`/help` + category index) · `disbot/cogs/help/`
> (route · panels · schemas) · `disbot/services/help_catalogue.py` (HLP-2 inventory + drift checks) ·
> `disbot/services/help_projection.py` (the one reason-coded access seam, 5 render paths) ·
> `disbot/services/help_overlay.py` + `help_overlay_mutation.py` (HLP-3 guild overlay, audited write
> seam, migrations 064/067) · `disbot/views/help/editor.py` + `home_builder.py` (the editor UI) · folio

> Assessed during the completion-first arc (Q-0209). Help is the **discoverable, governance-aware help**
> surface: all five render paths (Home category index, typed hub/subsystem routes, typed command embed,
> dropdown, dedicated `build_help_menu_view` panels) compose **one** `HelpProjection` (reason-coded
> states; only display/governance-hidden states hide — lock states stay advertised), and a per-guild
> **overlay** (hide/rename/re-describe + Home message) writes through the **single audited**
> `help_overlay_mutation` seam (administrator re-checked at callback **and** in the mutation, stable-key
> validation, cache invalidation, audit). Presentation-only (Q-0055: never affects execution). Strong
> test suite (~2,200 lines, zero registry-drift pinned). The honest gaps are convenience deepening
> (full-text search across subsystems; subcommand-level help) and the live walkthrough.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — discoverable, governance-aware help for every subsystem (~40 cogs
      expose `build_help_menu_view`) + a guild overlay to hide/rename/re-describe; five render paths on
      one projection.
- [x] **Every best-in-class sub-option** — category index + typed routes (hub/subsystem/command) + guild
      overlay + Home customization; search/subcommand help are the deepening gaps → punch #1/#2.
- [x] **Failure modes honest** — overlay DB fault → registry defaults (logged); orphaned overlay rows
      preserved + reported; unknown tier → user-floor fallback.
- [x] **Idempotent** — all-None overlay row deleted (= default, byte-identical); absent row = default.

### B. Reachability & UI
- [x] **The help menu IS the panel** — `!help`/`/help` + the mother-hub category dropdown; every cog's
      `build_help_menu_view` hook routes to its panel.
- [x] **Reachable every natural way** — `!help` + typed routes + Settings "Help appearance" + staff-hub
      "✏️ Help editor" (Q-0032: no new command names).
- [N/A] **Integrated into Setup** — Help is always-on discovery; the overlay editor is the config surface.
- [x] **Return navigation** — "↩ Back to Help" on non-subsystem panels (re-resolves governance); editor
      picker→entity→modal flow.
- [x] **In-place, not spammy** — slash ephemeral; editor ephemeral; "👁 Help Preview" beside the editor.

### C. Convenience
- [x] **Categories + typed jump** — mother-hub category index + `!help <hub|subsystem|command>` resolve
      to one destination (route dedup).
- [ ] **Search across subsystems** — ❌ no full-text command/description search; browsing + single-name
      routes only. → punch #1.
- [x] **Clear feedback** — editor shows override counts + orphan report + Q-0058 custom+default+key
      display; Home builder requires a preview before save (preview-is-exact).

### D. Authority & safety
- [x] **Authority re-checked at callback** — `_EditorViewBase.interaction_check` re-checks administrator
      at every callback **and** the mutation re-validates (`_check_admin`).
- [x] **All overlay writes through the audited seam** — `help_overlay_mutation` (`set_overlay_fields` /
      `set_home_message` / `reset_guild_overlay`) is the sole writer; emits `audit.action_recorded`;
      cache invalidated; views never touch the DB.
- [N/A] **Provisioning pipeline** — no resource creation.
- [x] **Reuses governance** — projection re-solves visibility per invocation; the overlay is
      presentation-only (Q-0055: admission paths never read it).

### E. Configuration
- [x] **Overlay via the audited seam** — per-guild hide/rename/re-describe + Home title/body/color
      (migrations 064/067), partial-edit UNSET/None merge semantics, bounds enforced.
- [x] **config-input widgets** — `HelpEditorHomeView` → `EntityPickerView` (paginated, Q-0058) →
      `HelpEntityEditorView`; `HomeMessageBuilderView` (draft→preview→save).
- [x] **Discovery** — SubsystemSchema "Help appearance" domain (capability `help.settings.configure`);
      Settings + staff-hub entry points.

### F. Wiring & discoverability
- [x] **Registry** — key `help`, capabilities `help.menu.view` + `help.settings.configure`, entry `help`,
      ui_priority 1, `supports_dm: True`.
- [x] **Discoverable in Help** — it IS Help; the customization catalogue picks up the help hooks.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_help_catalogue.py` (identity + **zero drift** pinned),
      `test_help_projection.py` (state vocabulary, 5 paths, governance-as-hider, lock-advertised),
      `test_help_render_paths.py` (5 paths + overlay hide/rename byte-identical-absent).
- [x] **Authority tests** — `test_help_editor.py` (non-admin denied at callback; admin passes);
      `test_help_overlay_mutation.py` (actor required, non-admin rejected, bounds, validation).
- [x] **Mutation-seam tests** — `test_help_overlay_mutation.py` (writes/cache/audit) +
      `test_help_overlay.py` (cache, fault tolerance, orphan preservation).
- [ ] **Live walkthrough recorded** — pending → punch #3.
- [ ] **Owner ✔** — pending → punch #4.

## Punch-list (clear these to certify)
1. **Search across subsystems** *(owner, deepening)* — full-text search of command names/descriptions
   (today: category browse + single-name routes).
2. **Subcommand-level help** *(owner, deepening)* — expose per-command groups/subcommands (today:
   top-level commands per subsystem).
3. **Live walkthrough** *(owner / live-bot)* — `!help` across tiers → category → subsystem → back →
   typed routes; editor hide/rename → preview → user re-runs `!help`, confirms the live change; orphan
   survival + cache invalidation, with screenshots.
4. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_help_catalogue.py` · `…/test_help_projection.py` ·
  `…/test_help_overlay.py` · `…/test_help_overlay_mutation.py` · `tests/unit/views/test_help_editor.py` ·
  `tests/unit/cogs/test_help_render_paths.py` · `tests/unit/help/*` (~2,200 lines total)
- **Walkthrough:** pending (punch #3) · **Owner sign-off:** pending (punch #4)

## Verdict
Help is one of the **most mature** server-fns assessed — five render paths on a single reason-coded
governance-aware projection, a per-guild overlay through a single audited mutation seam (admin
re-checked + cache + audit, presentation-only), an editor UI + Home customization, zero registry-drift
pinned, and ~2,200 lines of tests. It is **not yet `✔ certified`** only because of convenience deepening
(**search** #1, **subcommand help** #2) and the **live walkthrough/sign-off** (#3/#4). No safety/audit/
dead-end issues found.
