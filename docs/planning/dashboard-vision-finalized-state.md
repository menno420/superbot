# Dashboard — finalized-state vision (the bot's website + configuration control plane)

> **Status:** `plan` — north-star vision (2026-06-16). **Not an execution tracker** and **not a parallel
> source of truth.** This is the *destination* the dashboard converges toward; the *near-term build* lives
> in two execution plans this doc sits above:
> [`developer-dashboard-plan.md`](developer-dashboard-plan.md) (live record + phase roadmap) and
> [`dashboard-live-editor-plan.md`](dashboard-live-editor-plan.md) (the L0–L3 control-API + editor
> sequence). Where this doc and those plans differ on *what to build next*, **they win**; this doc only
> sets the long-horizon shape. Source code and merged PRs win over all three.
>
> **⚡ 2026-06-17 update:** the **write side shipped + activated** right after this doc was written — the
> live help / settings / cog-routing editors are running in production (owner logged in; bot logs show
> `control_api: enabled`). Several "Status today" cells below now understate reality; see
> **§ Reviewer note & post-activation status** for the corrected status and a full review.

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

## Reviewer note & post-activation status (2026-06-17)

*Reviewed by the session that **built and activated** the control panel — #993 (mutation endpoints),
#996 (OAuth login + editors), #1001 (IPv6 bind) — in the hours just before this doc merged. Net:
**a strong, correctly-structured north-star — adopt it.** One material status correction + four
refinements.*

**Verdict.** This is the right document. It correctly diagnoses the "three competing plans" drift and
resolves it by sitting *above* the two execution plans instead of beside them; the four-zone IA, the
3-ring authority model, the freshness/lineage contract, and especially the **manifest spine** are sound
and forward-looking. Nothing here contradicts what shipped.

**Material correction — the write side went live *today*, after this doc was written.** The phase table
and several "Status today" cells understate reality:

- **Phase C (OAuth + workspace) — partly shipped.** Discord OAuth login, a signed-cookie session, the
  `/admin` server picker, and per-guild editor pages are live (#996). *Still open:* the richer *read*
  workspace (`/me`, a server **overview** with setup-health, the authority preview) — those were skipped.
- **Phase F (first live writes) — shipped + activated.** The help / settings / cog-routing editors write
  live through the audited seams (#993 endpoints + #996 editors); `CONTROL_API_TOKEN` + the OAuth secret
  are set on Railway and it is confirmed working end-to-end.
- So the build **jumped C-auth → F-writes and skipped Phase E** (the control-API *read* endpoints for
  current values). That skip is the single most important consequence — see refinement 1.

**Refinements:**

1. **Elevate Phase E (current-value reads) to the immediate next priority.** The live editors currently
   write **blind** — they POST a new value but never show the server's *current* one, because the
   `/control/settings/current` + `/control/help/overlay` GET endpoints don't exist yet. This is the
   highest-value, lowest-risk next slice (much smaller than the manifest) and turns "edit blind" into
   "see-then-change." The doc lists it as Phase E but frames it as just-another-gated-phase; post-activation
   it is the *now* gap.
2. **Sharpen the manifest-spine gate.** The doc defaults the manifest (D) as a prerequisite "before live
   management of commands/panels." True for **commands/panels** — the AST `button_backed` flag is the real
   heuristic weakness. But settings/help/routing live management *already shipped* on their **already-typed**
   seams (`SettingSpec`, `help_overlay`, `command_routing` rows), which never needed the manifest. Reframe
   D's gate precisely: **the manifest gates command-management trustworthiness + the panel editor (H), not
   the settings/help/routing editors** — so the doc doesn't imply the shipped editors rest on shaky metadata.
3. **Flag the live hardening gap (security).** The panel is now **public + live**, but two of the doc's own
   mutation requirements aren't implemented yet: **rate-limiting** (none on the control API or the public
   login) and an **explicit CSRF token** (today only `SameSite=Lax` on the session cookie — real, but weaker
   than the stated CSRF-token requirement). Neither is a write-authorization hole (the bot still gates every
   write via the live member + seam), but since the surface is live, add a near-term hardening item:
   rate-limit the control API + login and add the CSRF token to the editor forms.
4. **Add the concrete Railway-IPv6 fact to § Security (service↔service).** "Railway private networking
   (Wireguard)" is right, but the operative gotcha (it cost a real fix this session, #1001) is that it is
   **IPv6-only**: the bot's health server had to bind `::` (dual-stack via `HEALTH_HOST`), not `0.0.0.0`, or
   `worker.railway.internal` is unreachable. Phase-E implementers need this.

*Minor:* the shipped session is a **stdlib HMAC-signed cookie** (no `itsdangerous`/middleware), satisfying
the doc's "signed session cookie" — and deliberately fewer deps to version-match. Recorded for accuracy.

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

### Homepage (finalized — owner decision: **hybrid router landing**)

The homepage is a **router landing** that adapts to the visitor (owner panel decision, 2026-06-16):

- **Logged-out / newcomers → a product tour:** hero + value proposition · feature bands per category
  (Moderation · Server Management · Economy · Games · AI · BTD6) · a live "trust band" (uptime/build/status)
  · use-case landing blocks ("start a community", "manage roles", "automate onboarding", "run minigames")
  · a clear **"Add the bot"** call to action.
- **Logged-in → straight to the workspace:** returning users skip the marketing and land on their personal
  overview / last server (an **"Open dashboard"** path, not a re-pitch).

Today's operator-telemetry-heavy homepage content moves to `/status` and the owner zone either way. (This
supersedes a pure product-marketing homepage: newcomers still get the product story, but regulars get a
control plane, not a billboard.)

### Mobile (finalized — owner decision: **full management on mobile**)

Mobile is **not** the collapsed desktop sidebar. Compact layout switches to **bottom navigation** (Home ·
Servers · Search · Activity · Account); everything deeper goes through in-screen nav, accordions, and
page actions. **Owner decision (2026-06-16): full management must work on a phone** — not just oversight.
That makes mobile a **first-class constraint on every editor**, not an afterthought: settings forms, the
help editor, command/cog toggles, and (eventually) the panel-layout editor all need a genuinely usable
compact layout (single-task screens, large touch targets, step-wise flows for batch edits, a mobile panel
preview). This raises the design bar across the authenticated zones and should be a per-screen acceptance
criterion, not a desktop-first build with a mobile fallback.

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
  website state or client code. **Operative gotcha (cost the #1001 fix):** Railway private networking is
  **IPv6-only** — the bot's health/control server must bind `::` (dual-stack via `HEALTH_HOST`), *not*
  `0.0.0.0`, or `worker.railway.internal` is unreachable. Phase-E implementers need this.
- **Live-surface hardening (reviewer note R3, not yet done):** the panel is public + live but still lacks
  **rate-limiting** (control API + the public login) and an **explicit CSRF token** (today only
  `SameSite=Lax` on the session cookie). Neither is a write-authorization hole — the bot still gates every
  write via the live member + seam — but both are near-term hardening items now that the surface is live.
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
| **C — OAuth + personal/server workspaces** | Login, sessions, `/admin` server picker, per-guild editor pages | `dashboard-live-editor-plan.md` L0 | 🟡 **partly shipped + live** (#996): OAuth login + server picker + editor pages run; **still open** — the richer *read* workspace (`/me`, a server **overview** with setup-health, the authority preview) |
| **D — manifest spine** | Typed command/panel/settings manifest export + panel registry + reconciliation tests; AST demoted to drift detection | **NEW track** (this doc) | ✅ **approved (Q-0162).** Gates **command-management trustworthiness + the panel editor (H)** — *not* the already-shipped settings/help/routing editors (they ride already-typed seams). Build after the Phase-E reads, before H. |
| **E — control API read endpoints** | Private, secret-protected reads: **current settings values**, help overlay, server context, capabilities, diagnostics, manifest | `dashboard-live-editor-plan.md` L1 | ⚠️ **SKIPPED — now the top next priority.** The token is set, but the current-value **GET** endpoints (`/control/settings/current`, `/control/help/overlay`) were never built, so the live editors **write blind** (see reviewer note R1). Highest-value, lowest-risk next slice. |
| **F — first live writes (audited seams)** | Help / settings / cog-routing editors over the audited seams | `dashboard-live-editor-plan.md` L2 + Q-0157 | ✅ **SHIPPED + LIVE** (#993 endpoints + #996 editors) — confirmed end-to-end. Order help → settings → aliases/routing (Q-0163); **aliases live-overlay + global-settings tier still to come.** |
| **G — owner zone: env values + control board** | Masked Railway value mgmt; idea/bug triage; multi-AI control board over the `/fire` routines | `developer-dashboard-plan.md` Phases 3b/4 | owner: Railway API creds; **owner-only, scope-shaped** (Q-0162) |
| **H — panel-layout engine + editor** | DB-backed `panel_layout` overlay + render-time reader + audited seam, **then** the drag-and-drop editor | `dashboard-live-editor-plan.md` L3 | manifest spine (D) + panel registry; **scheduled last** (Q-0163) |

> **Status reconciled (2026-06-17, with the reviewer note above):** the write side **shipped and went
> live** right after this plan was written — the build jumped **C-auth → F-writes and skipped Phase E**
> (the current-value read endpoints). So the setup gate is cleared *and then some*: live editing works,
> but **the live editors write blind until Phase E lands** — which is why E is now the **top next
> priority**, not a future phase. Near-term hardening the live surface still needs: **rate-limiting** +
> an **explicit CSRF token** (reviewer note R3).

## Decisions (owner question-panel, 2026-06-16 — all forks resolved)

The owner answered all open forks via the question panel. These are now **decided**, not defaults;
provenance is router **Q-0162** (the two architectural forks) and **Q-0163** (the rest).

| Fork | Decision | Note |
|---|---|---|
| **Manifest spine — go/no-go + priority** | **Build it — gating *command-management trustworthiness + the panel editor (H)*, after the Phase-E reads** | Sharpened post-activation (reviewer note R2): the shipped settings/help/routing editors ride **already-typed** seams and never needed the manifest; the manifest's real job is the AST `button_backed` weakness — i.e. commands/panels. (Q-0162) |
| **Owner-zone future scope** | **Owner-only now, but scope-shaped** for later delegated roles | Structure routes/authority so adding limited scopes (observability-only · issue-triage · content-editing · runtime-control) later is an add-on, not a rewrite. No delegated roles built until asked. (Q-0162) |
| **Homepage emphasis** | **Hybrid router landing** | Newcomers → product tour; logged-in → straight to workspace. (Q-0163) |
| **Authority UX posture** | **Cautious edits, open info** | Show edit controls only when near-certain allowed; show read-only info + the authority preview freely. (Q-0163) |
| **First live-write order** | **Help → settings → aliases/routing → panels** | Lowest architectural resistance first; global-settings runtime tier built in parallel. (Q-0163) |
| **Mobile management depth** | **Full management on mobile** | Not just oversight — a first-class per-screen design constraint on every editor. (Q-0163) |
| **Panel-layout editor timing** | **Last**, after the simpler editors | Greenfield bot-side panel-layout model is the prerequisite; build it once help/settings/routing editors are proven. (Q-0163) |
| **Owner setup readiness** | **Already complete & confirmed working** | Discord OAuth + control token set on Railway → phases C/E/F are no longer owner-setup-gated. (Q-0163) |

**Remaining open items are implementation-level only** (not owner-gating): the dashboard session store
(signed cookie vs. its own Postgres) and whether a "global default" help overlay is ever wanted — both
decided at their build phase, per the two execution plans' own open-questions sections.

## References

- Execution plans (authoritative for *what to build next*):
  [`developer-dashboard-plan.md`](developer-dashboard-plan.md) ·
  [`dashboard-live-editor-plan.md`](dashboard-live-editor-plan.md)
- Owner decisions: router **Q-0155–Q-0160** (`docs/owner/maintainer-question-router.md`) and the new
  **Q-0162** + **Q-0163** (the question-panel decisions — see § "Decisions (owner question-panel,
  2026-06-16)").
- Seams this fronts: `services.settings_mutation` · `services.help_overlay_mutation` ·
  `services.command_routing` · `services.participation_mutation` · `core/runtime/command_surface_ledger.py`
  · `disbot/control_api.py` (the dormant foundation, #989).
- Inputs synthesized: the owner's uploaded deep-research report + Codex PR #998 (closed in favor of this
  doc; its route-trust inventory, data-trust matrix, manifest schema, and readiness framing are folded in
  above).
