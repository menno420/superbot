# Server Management Hub — PR14 implementation plan

> **Status:** `plan` — planned end-state; cross-check source before implementing.
> **Created:** 2026-06-08 · **Owner area:** server management
> (folio: [`docs/subsystems/server-management.md`](../subsystems/server-management.md)).
>
> This is the **last** server-management PR (the implementation plan's PR14). It
> depends on all the specialized managers, which have shipped. Authoritative
> sequence: [`server-management-status-2026-06-05.md`](server-management-status-2026-06-05.md).
> Companion scope detail: the implementation plan's
> [PR14 section](server-management-implementation-plan-2026-06-05.md).

## Objective

One **navigation** surface — a persistent `!servermanagement` hub (+ aliases) and
an ephemeral `/server-management` — that gives an operator a single entry point to
the moderation / channel / role / cleanup / setup managers, with **read-only
health badges** summarising what needs attention, and **per-callback authority
re-checks** (ADR-005). The hub holds **zero domain logic**: it *composes* the
existing manager panels and read-only health services, never re-implementing them.

## Scope (what PR14 builds)

1. A shared **hub builder** (`build_server_management_hub(...)`) returning
   `(embed, view)`, used by both the prefix and slash entry points (one builder,
   two front doors — mirrors `views/games/hub.py::build_games_hub_panel`).
2. `ServerManagementHubView(PersistentView)` — one button per manager + the
   standard navigation, restored across restart via the anchor manager.
3. A persistent `!servermanagement` command (+ aliases `!servermenu`,
   `!guildmenu` — confirm none collide) on a new lightweight cog (or the existing
   admin/utility cog — see "Decisions").
4. An ephemeral `/server-management` slash that calls the same builder.
5. **Read-only health badges** composed from the existing detectors (no new
   detection): per-manager status glyph + a one-line overall summary.
6. **Authority**: a panel-level `interaction_check` (administrator floor) plus a
   per-callback re-check that matches each target manager's own authority before
   routing into it.

## Out of scope (explicitly)

- No new mutation path, op-kind, migration, or service. Every action still happens
  inside the manager panels PR14 routes to.
- No second "danger dashboard" / readiness ledger — extend `ReadinessSnapshot`
  reads, don't fork them (`docs/ideas/future-product-direction…` rejection ledger).
- No AI, no web surface (owner intent Q-0002: Discord-first; keep read models
  reusable so a web companion is *possible*, don't start it).

## Architecture (source-grounded)

### Reuse seams — route to existing manager factories, don't rebuild

Each manager already exposes an async factory that returns its panel embed+view.
The hub's buttons call these (compose canonical owners; never duplicate):

| Manager | Entry | Factory to reuse |
|---|---|---|
| Moderation | `!modmenu` | `cogs/moderation_cog.py:84` `build_help_menu_view()` → `ModPanelView` (`views/moderation/main_panel.py:35`) |
| Channels | `!channelmenu` | `cogs/channel_cog.py:155` `build_help_menu_view()` |
| Roles | `!roles` | `cogs/role_cog.py:354` `build_help_menu_view()` → `RoleHubPanelView` (`cogs/role_cog.py:70`) |
| Cleanup | `!cleanup` | `cogs/cleanup_cog.py:414` `build_help_menu_view()` |
| Setup | `!setup` | `views/setup/hub.py::SetupHubView` (open the wizard hub) |

> **Verify before building** (the Explore map inferred some of these): confirm each
> `build_help_menu_view()` signature (args, whether it takes `interaction`/`ctx`)
> and that calling it from another cog is clean (it is the Help-menu seam, so it is
> meant to be reused). For Setup, decide whether to open `SetupHubView` directly or
> point the operator at `!setup` (the wizard owns its own session/depth flow).

### Base classes + exemplars

- **`PersistentView`** — `core/runtime/persistent_views.py:45`. Requires
  `SUBSYSTEM` classvar, `@register`, static `custom_id`s `"{SUBSYSTEM}:{action}"`,
  and **stateless** design (recover context from `interaction` + DB, never instance
  state). Set `FAIL_CLOSED_ON_MISSING_ANCHOR = True` (this is an operator/owner
  panel — fail closed if the anchor is gone, matching `RoleHubPanelView`).
- **Restoration** — `core/runtime/message_anchor_manager.py:110 restore_anchors(bot)`
  at `on_ready` re-instantiates `view_cls()` and `bot.add_view(...)`. Upsert an
  anchor `(user_id, guild_id, channel_id, subsystem="server_management", message_id)`
  when the hub is posted.
- **Structural template:** `views/games/hub.py` (persistent multi-button nav hub
  with click-time governance recheck + back-button closure) is the closest
  exemplar; `views/moderation/main_panel.py:45 interaction_check` is the authority
  gate to mirror. Binding rules: `docs/building-roadmap/hub-ui-standard.md`
  (Operator Hub shape) + `docs/runtime_contracts.md` §3 (PersistentView contract).

### Authority (ADR-005 / `docs/capability-authority.md` §4)

- Panel-level `interaction_check`: administrator floor (the hub aggregates admin
  surfaces), via `core/runtime/ui_permissions.can_execute(interaction, …)` /
  `interaction_is_admin` (`views/base.py:86`).
- Per-callback re-check **before routing into a manager**: match that manager's
  authority (e.g. the Moderation button admits on `moderate_members` OR the
  moderation capability, exactly like `ModPanelView.interaction_check`). A button
  the caller can't use renders **disabled with a reason**, not hidden, so the hub
  explains *why* (the "what happens next" ethos).
- Re-check **target guild** at click time (the panel may be restored in a guild the
  caller no longer administers).

### Health badges (read-only composition — no new detection)

Compose, per render, into a compact per-manager glyph + a one-line summary:

| Source | Function | Use |
|---|---|---|
| `services/resource_health.py:109` | `inspect(guild) -> tuple[ResourceHealthFinding…]` | binding health (missing/stale/perm/hierarchy) |
| `services/setup_diagnostics.py:205` | `collect_setup_diagnostics(guild) -> SetupDiagnosticsReport` | blocker/warning/advisory counts (PR12) |
| `services/setup_readiness.py:166` | `collect(guild) -> SetupReadinessReport` | overall setup completeness |
| `utils/moderation_feasibility.py:61` | `evaluate_moderation_readiness(guild)` | can the bot ban/kick/timeout? |
| `utils/role_feasibility.py:121/161` | `evaluate_role` / `manageable_roles` | can the bot manage roles? |

Badge mapping: `🟢 healthy / 🟡 needs attention / ⛔ blocked` per manager, derived
from the worst finding severity in that manager's slice. Keep it a **best-effort**
read — a failed detector degrades to "unknown", never breaks the hub render
(mirror `setup_diagnostics`'s fail-safe collectors). **Bound the cost**: cache the
composed snapshot on the view for the render; recompute on an explicit "Refresh".

## Slice breakdown (≤2 PRs — risk-managed)

**PR14a — persistent hub foundation (the bulk).**
- `services/server_management_hub.py` (new, read-only) — the badge composer
  (`collect_hub_status(guild) -> HubStatus`) so the view stays render-only and the
  composition is unit-testable without Discord. Lives in `services/` so the future
  web companion (Q-0002) can reuse it.
- `views/server_management/hub.py` (new) — `ServerManagementHubView(PersistentView)`
  + `build_server_management_hub(...)`.
- A cog command `!servermanagement` (+ aliases) + anchor upsert + restoration wiring.
- Tests: badge composition (mocked detectors, fail-safe degradation), `custom_id`
  format + `@register` + `SUBSYSTEM`, panel `interaction_check` (admit/deny), each
  nav callback re-checks authority and routes to the right factory (mock the
  factories), restoration round-trip (anchor → `add_view`).

**PR14b — slash parity + polish (small; fold into 14a if it stays small).**
- Ephemeral `/server-management` calling the same builder.
- Disabled-with-reason rendering for managers the caller lacks authority for.
- "Refresh badges" button; back/close nav via `views/navigation.py:attach_back_button`.

## Risks & mitigations

- **Persistent-view restoration is hard to live-test in the sandbox** (needs a real
  restart + a posted anchor). Mitigate: unit-test the registration + a simulated
  `restore_anchors` path; do a real boot + `!servermanagement` + restart live-check
  on the maintainer's bot before calling it done.
- **Cross-cog factory coupling** — calling another cog's `build_help_menu_view()`
  introduces a `views → cogs` edge if done from a view. Keep the routing in the
  **cog/command layer** (the hub view emits an intent; the cog resolves the target
  factory), or have each manager register its factory into a small
  `diagnostics_service`-style provider (cogs register INTO a service — the clean
  direction, see the journal rule). **Decide this explicitly** (see Decisions).
- **Authority drift** — a restored panel outliving the caller's admin role. The
  per-callback + target-guild re-check is the guard; pin it with a test.
- **Badge cost on large guilds** — bound with the per-render cache + explicit
  refresh; never block the first paint on a slow detector.

## Decisions to make at PR time (defaults noted)

1. **Cog home:** new `server_management_cog.py` vs. extend an existing admin cog.
   *Default:* a new thin cog (one owner per hub; keeps cog LOC ceilings safe).
2. **Manager routing mechanism:** direct factory call from the command layer
   *(default, simplest)* vs. a registry where each manager registers its
   `(label, factory, authority)` into a service the hub reads *(cleaner boundary,
   slightly more wiring)*. Prefer the registry if the direct call forces a
   `views → cogs` import.
3. **Setup target:** open `SetupHubView` directly vs. route to `!setup`. *Default:*
   route to `!setup` so the wizard owns its session/depth lifecycle.

## Definition of done

- Both `!servermanagement` and `/server-management` render from **one** builder.
- The hub holds no domain logic; every action routes into an existing manager.
- Health badges are read-only, fail-safe, and bounded.
- Every callback re-checks capability + target guild (ADR-005); pinned by a test.
- Persistent restoration works (registration + anchor) — verified by a real
  restart live-check.
- `check_quality --full` + `check_architecture --mode strict` green; no new
  `services → views` or `views → cogs` violation introduced.

## Verify-before-building checklist (the Explore map flagged these as inferred)

- [ ] Exact `build_help_menu_view()` signatures for channels (`channel_cog.py:155`)
      and cleanup (`cleanup_cog.py:414`); confirm they're safe to call cross-cog.
- [ ] Channel/cleanup hub **view class** names + files (the map inferred
      `_ChannelManagerView` / `CleanupPanelView`).
- [ ] No existing `!servermanagement`/alias collision (grep confirmed none today).
- [ ] `setup_readiness.collect` return shape (the badge needs its score/findings).
- [ ] Whether routing from a view layer trips the `services → views` /
      `views → cogs` arch rules — drives Decision #2.
