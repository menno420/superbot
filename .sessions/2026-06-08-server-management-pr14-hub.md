# 2026-06-08 — Server-management PR14: the unified Server Management Hub

**Arc:** Orientation session — read the docs, confirmed state (PR13 deterministic +
the PR14 plan already merged; no open PRs), asked the maintainer which lane to advance.
He chose **PR14 (the Server Management Hub)** — the capstone. Built it end-to-end, then
hit an architectural fork mid-build (a registered persistent view with no matching
subsystem is an `auto_healable` identity-contract orphan), asked, and the maintainer chose
**"make it a first-class subsystem."** Registered it, re-verified, shipped.

**Shipped (one PR — read-only composition, low risk):**
- `services/server_management_hub.py` — read-only, **fail-safe** badge composer
  (`collect_hub_status(guild) -> HubStatus`): per-manager capability glyphs from the
  existing detectors (`moderation_feasibility`, `role_feasibility`, Manage-Channels perm) +
  a cross-cutting config-health line from `setup_diagnostics` + a `setup_readiness` %.
  Never raises (broken detector → ❓). In `services/` so a future web companion reuses it.
- `views/server_management/hub.py` — `ServerManagementHubView(PersistentView)`: one button
  per manager + Refresh. Routes via `interaction.client.get_cog(...).build_help_menu_view`
  (the proven Games-hub pattern) with Back-to-hub attached → **no module-level `cogs`
  import**. **Admin-floor `interaction_check`** (mirrors `ModPanelView`, not anchor
  ownership) so the one view backs both the anchored prefix panel and the anchorless
  ephemeral slash. Setup delegates to `open_wizard_from_slash` (lazy import).
- `cogs/server_management_cog.py` — thin cog: `!servermanagement` (+ `servermenu`/`guildmenu`)
  anchored via `panel_manager.get_or_render_panel`, ephemeral `/server-management`, and a
  `build_help_menu_view` help hook. Added to `INITIAL_EXTENSIONS`.
- **First-class registration (owner decision Q-0016):** `SUBSYSTEMS["servermanagement"]` +
  a `HUBS` entry (administrator tier) + a `KNOWN_PANEL_COMMANDS` entry; key is
  `servermanagement` (no underscore — matches `cog_name_to_subsystem`). Updated the
  hub-set / help-category / discoverability enumeration tests + the help-surface-map (§1+§2)
  and the settings-customization command-map (`### servermanagement` section).

**Verification:** full CI mirror green (`check_quality --full`: **8062 passed**, 3 skipped);
`check_architecture --mode strict`: 0 errors; **live boot clean** — `ServerManagementCog
loaded`, view registered under `servermanagement`, **`Identity-contract: clean … STRICT=on`**
(the orphan finding the standalone-view variant produced is gone), 0 ERROR/CRITICAL. New
tests: `test_server_management_hub.py` (service) + `test_server_management_hub_view.py` (view).

**Gates / next:** Server-management is **structurally complete** — the only remaining item is
the **gated PR13 AI generation layer** ("Generate with AI" role templates; behind the
AI-expansion gate + not live-testable here without provider keys). Restart-restoration +
a real operator click-through remain for the maintainer's bot. With the lane otherwise done,
the next session should pick the next lane from `docs/roadmap.md` or groom `docs/ideas/`.
Authoritative queue: `docs/planning/server-management-status-2026-06-05.md` (PR14 subsection).

## Context delta
- **Needed but not pointed to — the "add an operator hub" wiring is an 8-place contract.**
  Making a hub first-class touches: (1) `SUBSYSTEMS` + (2) `HUBS` + (3) `KNOWN_PANEL_COMMANDS`,
  (4) a `build_help_menu_view` cog hook, (5) help-surface-map §1+§2, (6) command-map
  `### <subsystem>` section, (7) the hub-set / help-category / discoverability **enumeration
  tests**, and (8) a registry **key that equals `cog_name_to_subsystem(Cog)`** (strips
  "Cog"+lowercases, **no** underscore insertion → `ServerManagementCog` ⇒ `servermanagement`).
  That key must also be the view `SUBSYSTEM` + the `get_or_render_panel` anchor string, or the
  identity-contract (view) + ledger (orphan-cog) + db-anchor findings persist. Nothing names
  this checklist in one place — captured a short version in the folio debug-router this session.
- **Needed but not pointed to — the identity contract is the signal that "hubs are
  subsystems."** A registered `PersistentView` whose `SUBSYSTEM ∉ SUBSYSTEMS` is classified
  `auto_healable` (`!platform identity --fix` would *unregister* it). That, plus the fact that
  every existing hub is a subsystem, is why the maintainer chose first-class. The folio /
  hub-ui-standard don't state this.
- **Pointed to but didn't need:** CodeGraph (available this session) — grep + the PreToolUse
  `context_map.py` (importers / blast-radius / lazy-import surfacing) carried the whole
  investigation, exactly as on 2026-06-08's PR13 session. The PR14 plan's exemplar choice
  (`RoleHubPanelView`, an ownership panel) needed correcting to `ModPanelView` (the
  authority-gated exemplar), and the plan didn't anticipate the registration fork.
- **Discovered by hand:** `interaction.client` is typed `discord.Client` (no `get_cog`) →
  needs `# type: ignore[attr-defined]` (GamesHubView sidesteps via `_cog_for_subsystem` +
  `arg-type` ignore). The discoverability invariant derives the cog filename from the
  subsystem key (`{key}_cog.py`), so a module named `server_management_cog.py` with key
  `servermanagement` is invisible to it — resolved via the `KNOWN_PANEL_COMMANDS` floor.

## Idea-backlog grooming (standing secondary task, Q-0015)

Browsed `docs/ideas/`. The three captures are each in a routed state: the mining-brainstorm
`!explore` wiring was promoted to a plan + roadmap horizon (#581); `ai-extra-tool-capability-ideas`
stays parked behind the AI-orchestration gate; `future-product-direction-2026-06-07` is an
explicit **capture-only** doc whose items were nearly all **gated _after_ server-management**.
**The grooming signal this session:** server-management is now structurally complete (PR14),
so that gate has cleared — the **next session should re-examine `future-product-direction`'s
server-management-gated items and route the now-unblocked ones onto a `docs/roadmap.md`
horizon.** No unilateral promotion this session (the doc is capture-only + I own the live PR
#584); the trigger is recorded here and the next-lane pointer is in `current-state.md`'s
▶ Next action. No idea left orphaned.
