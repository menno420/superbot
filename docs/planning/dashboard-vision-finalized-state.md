# Dashboard — finalized-state vision (the bot's website + configuration control plane)

> **Status:** `plan` — north-star vision (2026-06-16). **Not an execution tracker** and **not a parallel
> source of truth.** This is the *destination* the dashboard converges toward; the *near-term build* lives
> in two execution plans this doc sits above:
> [`developer-dashboard-plan.md`](developer-dashboard-plan.md) (live record + phase roadmap) and
> [`dashboard-live-editor-plan.md`](dashboard-live-editor-plan.md) (the L0–L3 control-API + editor
> sequence). Where this doc and those plans differ on *what to build next*, **they win**; this doc only
> sets the long-horizon shape. Source code and merged PRs win over all three.

## Why this document exists

The owner uploaded an external deep-research report on the dashboard, and Codex opened PR #998 with a
parallel review. Both are thoughtful and largely correct — but both **re-derive conclusions the repo had
already reached** (Discord OAuth, private bot-side control API, audited-seams-only writes, no parallel
source of truth) and land them in *new* plan docs, which risks three competing dashboard plans drifting
apart. This document is the **single north-star** that resolves that: it keeps the genuinely-additive
ideas from both reviews, folds them onto what is already **shipped and decided** (Q-0155–Q-0160), and
positions the two existing plans as its execution tracks. PR #998 is closed in favor of this doc.

**What was genuinely additive** (and is captured below): the per-route **trust inventory** and **data
trust matrix** (#998); the typed **command/panel/settings manifest spine** as the long-term metadata
source of truth (both reviews — the repo does not yet have this); the full **4-zone information
architecture + navigation model** (top-nav + workspace sidebar + command palette + canonical detail
routes); the **3-tier freshness contract**; and the **3-ring authority** framing. Everything else in the
reviews was already in the two execution plans or in the shipped code.

## North star (one paragraph)

SuperBot's website becomes a **schema-driven control plane** in front of the bot — never a second
configuration system. It does three things well: makes the right things **discoverable** (a credible
public product site + searchable catalogues), makes the right rights **visible** (an honest authority
preview so people see what they may read vs. change *before* they try), and calls the right bot seams
**safely** (every write flows through an existing audited mutation seam over a private control API, with
the bot — never the browser — as the final authority). The bot stays the source of truth and remains
fully manageable from inside Discord; the website is a faster-oversight shortcut layered on top. The
finished site has four clearly-separated zones (public · personal · server-admin · owner/developer), a
navigation model that scales from a marketing homepage to a deep per-server workspace, and a metadata
backbone (the manifest spine) reliable enough that the UI never offers a control the runtime can't honor.

## The two binding principles (carry forward from Q-0158 — never violate)

1. **The bot is the source of truth and the top priority.** Everything must stay fully manageable *in the
   bot itself*. The website is a shortcut for faster oversight, never the *only* way to do something, and
   never owns a copy of the truth.
2. **Front-end existing audited seams — never build a parallel system.** Every write the website performs
   goes through an existing, audited bot mutation seam over the control API. The website renders current
   state and drives those seams; it stores only a session (who you are), never a second copy of config.

These two lines are the test every future dashboard PR must pass.

## The four zones (the control-plane layers)

The finished site separates four zones with **different authority models, information needs, and failure
impact** — keeping them distinct is what keeps navigation legible and the security review tractable
(mixing them is the report's "context-vermenging" anti-pattern).

| Zone | Who | Purpose | Auth | Status today |
|---|---|---|---|---|
| **Public** | anyone, logged-out | Product showcase + read-only catalogues (commands, functions, games, settings reference, access/visibility map, ideas, bugs, updates, env-usage, status). Build trust that the project is alive. | none | **Shipped** (all read-only surfaces live) |
| **Personal** | any Discord user, logged-in | "What can I manage / what's mine?" — profile & per-user preferences (the `user_participation` seam), the user's servers, an authority preview. The hinge between public site and server management. | Discord OAuth | Planned (needs OAuth) |
| **Server-admin** | a guild's admins | The primary workspace: per-server overview (setup health, missing bindings, invalid settings, recent changes/activity) → settings · help appearance · command/cog routing · aliases · panels. | OAuth + **bot-side** per-guild authority | Read models partly shipped; live edits gated |
| **Owner / developer** | the bot owner (later: scoped operators) | Platform control, *not* guild management: project/deploy/build status, env-var **value** management (via Railway), idea/bug triage, the multi-AI control board, operator diagnostics. | owner gate (stricter) | Partly shipped (`/status`, `/env` usage map); value-mgmt + control board gated |

The owner/developer zone lives behind its **own** stricter gate and its own sidebar (the report's
`/studio` or `/owner` idea), so the jump from "managing a server" to "managing the platform" is visually
and authorization-ally unambiguous.

## Information architecture & navigation model (finalized)

No single nav pattern fits the whole site; the finished site uses a **hierarchy** of patterns:

- **Public routes → simple top-nav** (Product · Modules · Commands · Status · Roadmap/Bugs · Login). No
  sidebar on the marketing surface.
- **Authenticated routes → a workspace shell with a context sidebar** whose contents switch by zone:
  - *Personal:* Overview · Servers · Activity · Profile.
  - *Server:* Overview · Settings · Commands · Panels · Help · Access · Audit · Diagnostics.
  - *Owner:* Status · Deploys · Env · Ideas · Bugs · Secrets · AI Control.
- **A command palette / global search as an accelerator, not primary nav** — "go to server", "open
  subsystem", "find command/setting/capability", "open audit", later owner actions ("invalidate cache",
  "run health check"). This is what makes the dashboard feel sharper than typical bot dashboards (which
  rely only on cards + tabs).
- **Cards only on overview screens** (homepage, personal overview, server overview); detail management
  drills into **canonical, deep-linkable routes** with breadcrumbs and (later) audit history:
  - `/servers/{guild}/overview`
  - `/servers/{guild}/settings/{subsystem}`
  - `/servers/{guild}/commands/{qualified_name}`
  - `/servers/{guild}/panels/{panel_id}` (read-only until the panel-layout model exists)
  - `/servers/{guild}/help`, `/aliases`, `/audit`
  - personal: `/me`, `/me/servers`, `/me/profile`, `/me/authority`
  - owner: `/owner/ops`, `/owner/env`, `/owner/deploys`, `/owner/control-board`, `/owner/audit`

### Homepage (finalized)

Becomes a real product homepage with live-project credibility on top: hero + value proposition · feature
bands per category (Moderation · Server Management · Economy · Games · AI · BTD6) · a live "trust band"
(uptime/build/status) · use-case landing blocks ("start a community", "manage roles", "automate
onboarding", "run minigames") · a clear split between **"Add the bot"** and **"Open dashboard"**. Today's
operator-telemetry-heavy homepage content moves to `/status` and the owner zone.

### Mobile (finalized)

Mobile is **not** the collapsed desktop sidebar. Compact layout switches to **bottom navigation** (Home ·
Servers · Search · Activity · Account); everything deeper goes through in-screen nav, accordions, and
page actions. Default posture: **mobile-first for quick oversight + light single-task edits**; heavy
editing (settings batches, panel layout) is a desktop/large-screen experience.

## The bot's configuration capabilities — finalized map

This is the heart of the owner's ask ("the bot's configuration capabilities"). The finished site exposes
**every** configurable surface the bot owns — each one **front-ending an existing audited seam**, at the
scope the bot supports. None of these are new config systems; the new work is the API + UI in front.

| Capability | Audited bot seam | Scope | Web affordance (finalized) | Status |
|---|---|---|---|---|
| **Per-server settings** | `services.settings_mutation.SettingsMutationPipeline` + `SettingSpec` (`cogs/*/schemas.py`) | per-guild | Typed forms from `SettingSpec` (default/hint/allowed-values), with default/current/effective side-by-side, inline validation, reset, audit context | Read model shipped (`/settings` + typed specs); live edit gated |
| **Global settings** | same pipeline + a **new global tier** (`resolve_setting`: per-guild → global → spec default) | global (owner) | Same editor with a **scope picker** ("Global (all servers)" vs a specific server); global owner-gated | New runtime tier needed (Q-0157) |
| **Per-user config / profile** | `services.participation_mutation` + `core/runtime/user_config.py` (`views/profile/`) | per-user | "Everyone configures it personally" — participation opt-in/out, subscription toggles, visibility, preference editors | Bot seam shipped (in-Discord editor #940); web surface gated on OAuth |
| **Help appearance** | `services.help_overlay_mutation` (migrations 064/067) | per-guild | Hide / rename / re-describe hubs & subsystems + Home message, with a **live Discord-embed preview** of default-vs-override before it goes live | Bot seam + in-Discord editor shipped; web editor is the first planned live write (L2) |
| **Command / cog routing** | `services.command_routing.set_policy` (migration 036) | per-guild, scope-aware (channel→category→guild) | Per-cog enable/disable toggle; per-command is a documented later bot layer | Read model shipped (#988); live toggle gated. **Per-command granularity = later (Q-0160)** |
| **Aliases** | `utils/synonyms.py` `COMMAND_SYNONYMS` (soft) | global (today) | Per-command alias box + global suggestion form; collision check; live overlay needs a per-guild alias model + seam | Suggest→PR shipped (`/aliases`, #982); live overlay is later work |
| **Panel button layout** | **none yet** — greenfield | per-panel | Drag-and-drop button rows, row-length warnings, mobile preview, authority preview, dry-run to a test server | **Blocked on a new bot-side panel-layout model** (L3) — do *not* fake it |
| **Env-var values** | Railway API (single source of truth) | platform (owner) | Masked view/edit behind owner login, audited; usage-map already public (names+locations only, never values) | Usage map shipped (`/env`); value mgmt gated (Phase 3b) |

**Sequencing note (resolves an apparent tension between Q-0157 and L2):** the **help editor is the first
*website* write** (lowest architectural resistance — help overlay is already data-driven + audited), while
the **global-settings tier** is a parallel **focused *runtime* PR** (it touches the hot `resolve_setting`
path) that unblocks the settings editor, which lands *after* help. Help-first on the web; settings
runtime groundwork in parallel. These do not conflict.

## Data & freshness architecture (finalized)

The finished site is a **hybrid**, never "everything live" and never "everything static":

1. **Public catalogues** keep loading the committed generated artifact (`dashboard/data/dashboard.json`)
   for speed and deploy-simplicity.
2. **Authenticated workspaces** read **live bot truth** through the private control API (current settings
   values, help overlay, capabilities, diagnostics, the command/panel manifest).
3. The website keeps a **short-TTL cache** with **explicit freshness labelling** — no view ever silently
   implies real-time when it isn't.

### Freshness contract (every data surface must declare its lineage)

Each surface carries provenance — `generated_at`, git SHA, scanner/manifest version, and (for live data)
the bot endpoint timestamp — and renders one of these **per-widget states**: `fresh` · `stale` ·
`fallback-static` · `unavailable` · `unauthorized`. Three honest lineage badges: **"generated"**
(commit/export-time), **"runtime-backed"** (live from the bot), **"planned live management"** (UI exists,
write not wired). HTTP `ETag` / `If-None-Match` / `stale-while-revalidate` improve read perf without
faking realtime.

### Route trust inventory (where the current generated data is trustworthy vs. approximate)

Folded from PR #998 — this is the map of what to badge and what to harden. `dashboard.json` is a
*committed generated artifact*: it can be internally consistent yet wrong about runtime reality because it
is AST/doc-derived, and it drifts whenever a source changes without re-running
`scripts/export_dashboard_data.py`.

| Route | Source / scanner | Trust level | Drift risk |
|---|---|---|---|
| `/healthz` | app constant | liveness only | doesn't prove data freshness or bot health |
| `/`, `/functions`, `/games` | `export_dashboard_data.py` (AST of `SUBSYSTEMS`) | mostly trustworthy for *declared* metadata | runtime registration/availability not proven |
| `/commands` | `scan_commands.py` + synonyms + catalogue | **mixed** — names/types useful; **button-backed is heuristic** | decorators drift from runtime; inherited/mixin/dynamic app-commands hard; view linkage inferred |
| `/aliases` | `scan_commands.py`, `scan_synonyms.py` | read-only suggestion aid | no live collision check against the loaded bot |
| `/settings` | `scan_settings.py` + `scan_setting_specs.py` | trustworthy for declared key/spec metadata; **not values** | no per-guild values; scanner can miss dynamic specs |
| `/access` | `scan_access.py` | verified static mirror of *visibility*, not execution authority | live member/guild-ownership state is runtime-only |
| `/ideas`, `/bugs`, `/updates` | markdown parsers over `docs/` + `.sessions/` | trustworthy docs index | not a live product board / submission store |
| `/env` | `scan_env_usage.py` | trustworthy for static code references; **no values** | dynamic env names / external config not shown |
| `/status` | export + app aggregation | dashboard inventory status, **not** bot/deploy truth | name implies "live" but currently lacks Railway/GitHub/bot probes |

### Data trust matrix (current source → finalized source of truth → mode)

| Data family | Today | Finalized source of truth | Dashboard mode |
|---|---|---|---|
| Public subsystem catalogue | static registry projection | `SUBSYSTEMS` + manifest checksum | static/hybrid |
| Command names / kinds | AST scan | runtime `bot.walk_commands()` + `tree.walk_commands()` via manifest, reconciled with the scanner | hybrid, freshness-badged |
| Aliases / synonyms | AST scan of decorators + `COMMAND_SYNONYMS` | runtime aliases + synonym registry (+ later owner-approved per-guild overlay) | hybrid |
| **Button-backed flag** | heuristic (`panel_action` / view tokens) | **explicit command/panel manifest with action IDs + panel registry** | **unverified until the manifest exists** |
| Settings keys / specs | static scans | `SettingSpec` registry from the bot + per-guild values via control API | static for docs, dynamic for values |
| Access / authority | static visibility map | bot `/control/authority` per user/guild/action | static education + dynamic enforcement |
| Help appearance | not in dashboard data | `help_overlay` read model via the bot API | dynamic after API read endpoints |
| Cog routing | read-only default/cog metadata | `command_routing` rows via the bot API | dynamic after API read endpoints |
| Health / deploy status | artifact metadata only | `/healthz` + bot `/control/ping` + Railway deploys + GitHub checks | dynamic widgets with graceful failure |

The preference hierarchy for keeping live data in sync: **(1) private request/response control API**
(default) → **(2) best-effort event push** for invalidation/activity feeds → **(3) a polled control-queue
table** only as a reserve if private networking is ever unavailable (the live-editor plan's fallback).

## The manifest spine (the key structural investment)

This is the most important *new* architectural idea from both reviews, and the repo does not have it yet.
Today command/panel metadata comes from an **AST scan** (`scan_commands.py`) — fine for read-only docs, but
fragile for management because it answers "does this *look* like a panel command?" not "*which* button, in
*which* panel, backing *which* command, with *what* authority?". The runtime
`core/runtime/command_surface_ledger.py` already carries richer business classifications
(`primary_entrypoint`, `panel_action`, `legacy_duplicate`, `internal_admin`, `hidden`, `deprecated`) —
closer to the truth than the AST. A hand-maintained registry alone would rot; Discord's app-command tree
export only covers slash commands.

**The finalized answer: a typed, bot-owned manifest built at startup** from runtime registrations +
explicit code annotations + `subsystem_schema`/`SettingSpec`/capability bindings + a **panel registry**,
exported as a reliable read artifact. AST becomes a **drift-detection layer**, not the source of truth.

```text
Sources
  A. Runtime registrations (prefix/slash/hybrid/tree)
  B. Explicit annotations / extras / classifications in code
  C. SubsystemSchema / SettingSpec / capability bindings
  D. Panel registry / layout model
  E. AST scanner (drift detection only)
        │
        ▼
  Startup builder ──▶ typed CommandManifest / PanelManifest / SettingsManifest
                        ├─▶ bot read APIs (control API)
                        ├─▶ generated dashboard export
                        └─▶ CI reconciliation tests
```

Minimum command/panel schema (per #998 — concrete enough to build against):

```json
{
  "version": 1, "generated_at": "...", "bot_build": "...",
  "commands": [{
    "qualified_name": "settings set", "kind": "prefix|slash|hybrid",
    "cog": "SettingsCog", "subsystem": "settings", "aliases": [],
    "classification": "primary_entrypoint|panel_action|...",
    "visibility_tier": "admin|...", "source": {"file": "...", "line": 123},
    "runtime_verified": true, "panels": ["settings:main"], "actions": ["settings:set"]
  }],
  "panels": [{
    "panel_id": "xp:main", "view_class": "XPMainPanel",
    "source": {"file": "...", "line": 1}, "layout_source": "hardcoded|db_overlay",
    "buttons": [{"action_id": "xp:config", "custom_id": "xp:config", "label": "Config", "row": 0, "command": "xp"}]
  }],
  "findings": []
}
```

Each manifest entry should minimally carry: canonical command id · human label · invocation kind ·
subsystem · cog · classification · manageability · capability requirements · visibility tier · aliases ·
slash name · panel target / open-view semantics · related settings keys · related bindings · auditability
· owner-only/internal flags · documentation source.

**Reconciliation tests (CI) that make the metadata trustworthy:**

- scanner output vs `dashboard.json`;
- scanner output vs `CommandSurfaceLedger` classifications;
- ledger vs `bot.walk_commands()` + `bot.tree.walk_commands()`;
- manifest command count vs the bot's status-embed count;
- panel registry vs view classes / custom IDs;
- committed `dashboard.json` vs a fresh export (a CI drift guard).

The **panel registry** (declarative descriptors beside the view classes) is the prerequisite for *any*
reliable panel-layout editor — and is the first half of the L3 "move buttons" work.

## Security & authority model (finalized)

**Three rings, and only the third is trusted:**

1. **Website UX gating** — what the UI shows. Cosmetic.
2. **Dashboard policy gating** — which routes/actions the site offers. Convenience.
3. **Bot-side final authorization** — the bot resolves the live `discord.Member` for `(user_id, guild_id)`
   and runs the **same capability check** every in-Discord surface uses
   (`governance.capability.actor_holds_capability`). **This is the only ring that may grant a write.** The
   browser's claim is never trusted on its own — the pattern the help-editor plan already mandates, applied
   to *every* read/write.

- **Identity = Discord OAuth** (`identify guilds`) — the IdP for ordinary users; no separate account
  system. Server-side OAuth, signed session cookie (`state` param for CSRF), minimal claims stored.
- **Service↔service = Railway private networking** (`*.railway.internal`, Wireguard) — the bot control API
  is **private only, never a public domain** — plus a shared `CONTROL_API_TOKEN` (bearer/HMAC) **and** the
  per-request admin re-check (defense in depth). Secrets live **only** in Railway variables, never in
  website state or client code.
- **Every mutation carries** actor id · guild id · idempotency/mutation id · CSRF token, is **rate-limited**
  (per IP/user/guild/action, and on public forms), and lands in the **bot's audit system** via the seam's
  `audit.action_recorded` emit. Structured logging (request id, actor, guild, action, result, latency) —
  never secret values.
- **Authority preview (the maturity feature):** because `/access` already separates *visibility* from
  *execution* and seams are capability-native, the site can literally show "you can see this · you may read
  this · you may change this · the bot is missing this binding · this write would be denied by capability
  X." Honest expectation-setting is what makes this dashboard more grown-up than typical bot dashboards.

## Anti-patterns to avoid (the report's risk list — all confirmed by repo policy)

1. **A parallel source of truth** "because the web feels faster." The #1 risk: drift, audit gaps, stale
   caches, race conditions. The audited-seams rule exists precisely to forbid this.
2. **Metadata drift** — building management UI against AST metadata that's only "probably" right; the UI
   thinks something is manageable and the runtime disagrees. The manifest spine is the cure.
3. **Context mixing** — collapsing server-admin, personal, and owner zones into one generic "dashboard"
   layer. Different authority models → keep them separate (the four-zone split above).
4. **Premature graphical panel editing** — panel buttons are hardcoded; drag-and-drop before the DB-backed
   panel-layout model is a mockup with no runtime value (or a messy bypass). **Model first, editor second.**

## Roadmap to the finalized state (phases)

The destination above is reached through the **existing** execution plans plus one new track (the manifest
spine). This roadmap is the *connective tissue*, not a re-plan — each phase points at its owning doc.

| Phase | Outcome | Owning plan / track | Gate |
|---|---|---|---|
| **A — public IA + product homepage** | Product-grade homepage; use-case taxonomy; better `/commands` & `/functions`; freshness badges everywhere | `developer-dashboard-plan.md` | none (no OAuth/runtime) |
| **B — freshness & provenance** | Lineage badges + per-widget states; automate export regen; ETag/conditional GETs | `developer-dashboard-plan.md` | none |
| **C — OAuth + personal/server workspaces (read-only)** | Login, sessions, `/me`, `/me/servers`, server overview, authority preview — the workspace shell *before* writes | `dashboard-live-editor-plan.md` L0 | owner: Discord OAuth secret + session secret |
| **D — manifest spine** | Typed command/panel/settings manifest export + panel registry + reconciliation tests; AST demoted to drift detection | **NEW track** (this doc) | architectural go/no-go → **Q-0162** |
| **E — control API read endpoints** | Private, secret-protected reads: server context, current settings, help overlay, capabilities, diagnostics, manifest | `dashboard-live-editor-plan.md` L1 | owner: `CONTROL_API_TOKEN` on both Railway services |
| **F — first live writes (audited seams)** | Help overlay/Home first; then global-settings tier + settings editor; then aliases/routing | `dashboard-live-editor-plan.md` L2 + Q-0157 | owner: prod pacing ("don't rush") |
| **G — owner zone: env values + control board** | Masked Railway value mgmt; idea/bug triage; multi-AI control board over the `/fire` routines | `developer-dashboard-plan.md` Phases 3b/4 | owner: Railway API creds; auth+DB decisions |
| **H — panel-layout engine + editor** | DB-backed `panel_layout` overlay + render-time reader + audited seam, **then** the drag-and-drop editor | `dashboard-live-editor-plan.md` L3 | manifest spine (D) + panel registry |

## Open questions (safe defaults in italics — the doc is actionable without answers)

These are captured here in full and the two architectural forks are routed to the question router as
**Q-0162** (the rest carry sensible defaults and don't block):

1. **Manifest spine — go/no-go + priority.** Should the bot invest in a typed runtime manifest as the
   long-term metadata source of truth (Phase D), demoting AST scanners to drift detection?
   *Default: yes, but sequence it after OAuth/read-only workspaces (C) and before live management of
   commands/panels, since reliable manageability metadata is the prerequisite for those editors.* → **Q-0162**
2. **Owner-zone future scope.** Owner-only forever, or designed now for later **delegated operator/mod
   scopes** (observability-only · issue-triage · content-editing · runtime-control)?
   *Default: build owner-only now but keep the owner zone's routes/authority scope-shaped so delegation is
   an additive grant later, not a permissions rewrite.* → **Q-0162**
3. **Homepage emphasis.** Primarily a public **product** site, or primarily a **dashboard** with a website
   shell? *Default: product homepage with a live-credibility trust band; operator telemetry moves to
   `/status` + the owner zone (per Q-0158 "main website").*
4. **Authority UX posture.** Conservative (show only near-certain-allowed actions) or liberal (show more
   with "final check on the bot" messaging)? *Default: conservative for **writes**, liberal for
   **reads/explainers** — the authority preview teaches without over-promising.*
5. **First live-write breadth.** *Default: help overlay → settings → aliases/routing → panel layout last
   (lowest architectural resistance first), with the global-settings runtime tier built in parallel.*
6. **Mobile management depth.** *Default: mobile-first for quick oversight + light single-task edits;
   heavy editing (settings batches, panel layout) is desktop.*

## References

- Execution plans (authoritative for *what to build next*):
  [`developer-dashboard-plan.md`](developer-dashboard-plan.md) ·
  [`dashboard-live-editor-plan.md`](dashboard-live-editor-plan.md)
- Owner decisions: router **Q-0155–Q-0160** (`docs/owner/maintainer-question-router.md`) and the new
  **Q-0162** (the two open forks above).
- Seams this fronts: `services.settings_mutation` · `services.help_overlay_mutation` ·
  `services.command_routing` · `services.participation_mutation` · `core/runtime/command_surface_ledger.py`
  · `disbot/control_api.py` (the dormant foundation, #989).
- Inputs synthesized: the owner's uploaded deep-research report + Codex PR #998 (closed in favor of this
  doc; its route-trust inventory, data-trust matrix, manifest schema, and readiness framing are folded in
  above).
