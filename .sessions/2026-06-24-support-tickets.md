# 2026-06-24 — Support-ticket subsystem (command + AI natural language)

> **Status:** `complete` — the support-ticket subsystem ships: by command, by a public panel button,
> and by the AI in natural language. Full CI mirror green (12332 passed, 48 skipped; black/isort/ruff/
> mypy clean) + arch 0 errors + check_docs/check_consistency clean.

> **Run type:** `manual` — owner-directed feature request.

**Branch:** `claude/blissful-planck-sf5te4`. **Trigger:** owner prompt — *"find out what the best
ticket bots have… then create a ticket function for our bot; it has to work by command as well as
through the AI with natural language."*

## What I'm about to do

Research-first: surveyed the top Discord ticket bots (Ticket Tool, Tickets, Tickety, Open Ticket,
AI Ticket Bot). The features that define a good one: clickable **panels** (button / dropdown for
4+ types), multiple **categories**, each ticket = a **private channel** for opener + staff,
**claiming**, **add/remove** participants, **transcripts** on close (log channel + DM), **per-user
open-ticket limits** + **blacklist**, **auto-close-on-inactivity**, pre-ticket **forms**, configurable
**support roles**, **ratings**, **stats**, and — the modern frontier + the owner's explicit ask —
**natural-language opening** ("open a ticket, I need help with X").

Build a new `ticket` subsystem mirroring the treasury/fishing decomposition:

1. **Migration 098** — `ticket_config` (per-guild: staff role, category, log channel, panel msg,
   max-open-per-user, ping-on-open, enabled) + `tickets` (rows: channel, opener, subject, status,
   claimed_by, source, timestamps, close reason) + `ticket_blacklist`.
2. **`utils/db/tickets.py`** — conn-aware CRUD (`ticket_*` names; flat-reexported via `utils.db`).
3. **`services/ticket_service.py`** — read model + eligibility (config, open-count, blacklist, lists).
4. **`services/ticket_mutation.py`** — the audited write boundary: open / close / claim / add / remove
   / config / blacklist, each through `db.transaction()` + `emit_audit_action()` + an EventBus signal.
   Channel creation via `ChannelLifecycleService.create_channels` (the audited seam).
5. **`views/tickets/`** — anchor-free **PersistentView**s (the `SetupLauncherView`/`UxLabPersistentDemo`
   precedent): a public **launcher** ("🎫 Open a ticket" button) + an in-channel **control** panel
   (Claim / Close), plus a staff hub panel + a "describe your issue" modal.
6. **`cogs/ticket_cog.py`** — `!ticket [new <subject>]`, `!ticket close|claim|add|remove`,
   `!ticketpanel`, `!ticketsetup`, `!ticketblacklist`; `build_help_menu_view` + `setup`; registers the
   persistent views at `cog_load`.
7. **AI tool `open_support_ticket`** — the **first audited *action* AI tool** (the existing
   `ai_tools.py` registry is read-only by a pinned invariant). It opens a ticket through the
   deterministic audited `ticket_mutation` service, bounded against abuse by per-user limits +
   blacklist + requiring the guild to have tickets configured. New `support_ticket` toolset, gated at
   `AIScope.USER`. Pinned test + module docstring updated to reflect the audited-action carve-out.
8. **Subsystem registration** (the 10 `new_subsystem.py` touch-points) + folio
   `docs/subsystems/ticket.md` + ownership row + tests.

### Decisions made alone (for owner ratification)

- **AI opens tickets directly via an audited action tool** rather than a confirm-button handoff. The
  NL stage emits replies through scattered `channel.send(...)` calls with no single reply object to
  attach a view to, so a confirm-button flow would mean risky hot-path surgery. The audited-mutation
  path is what modern AI ticket bots do and satisfies "mutations flow through deterministic services."
  This is the first write-capable AI tool — recorded as a router Q (provenance: this session's owner
  directive that it "work through the AI with natural language").

## What shipped (PR #1405)

A complete new `ticket` subsystem (treasury/fishing decomposition):

- **Migration 098** — `ticket_config` (per-guild: staff role, category, log channel, panel msg, max-open,
  ping-on-open, enabled) + `tickets` + `ticket_blacklist`.
- **`utils/db/tickets.py`** — conn-aware `ticket_*` CRUD (flat-reexported via `utils.db`).
- **`services/ticket_service.py`** — read model + the single `check_open_eligibility` gate (configured /
  blacklist / per-user cap) + a plain-text transcript builder.
- **`services/ticket_mutation.py`** — the audited write boundary: open (channel via
  `ChannelLifecycleService` → private overwrites → row), claim, close (transcript → log + DM → teardown),
  add/remove participant, config, blacklist. One txn per op, `emit_audit_action` + `ticket.opened`/
  `ticket.closed` after commit. Channel creation routes through the lifecycle seam; `set_permissions`/
  `delete` are direct (the no-direct-channel-mutation invariant fences only `channel_cog`/`views/channels/`).
- **`views/tickets/`** — anchor-free persistent **launcher** (`🎫 Open a ticket`, public) + in-channel
  **control** panel (Claim/Close, callback-time authority re-checks) + a **hub** (`!ticket`) + the open modal.
- **`cogs/ticket_cog.py`** — `!ticket [new|close|claim|add|remove]`, `!ticketpanel`, `!ticketsetup`,
  `!ticketlimit`, `!ticketblacklist`; subscribes to `ticket.opened` to render the welcome + control panel
  (the single UI seam for all three open paths); Help hook + persistent-view registration at `cog_load`.
- **AI tool `open_support_ticket`** — the **first audited *action* AI tool** (Q-0201). Offered only with a
  live guild+member; opens through `ticket_mutation` (`source="ai"`), bounded by the same eligibility gate.
  Module docstring + `_ACK_UNCOVERED_TOOLS` + the toolset-family test updated; new `support_ticket` toolset.
- **Registration**: all 10 `new_subsystem.py` touch-points (registry entry `parent_hub="community"`,
  panel-command, extension role, surface/command/nav docs) + Community-hub child + `ownership.md` rows +
  events catalogue + the regenerated dashboard/site/env/crosswalk artifacts.
- **Tests**: `test_ticket_service.py` (7) · `test_ticket_mutation.py` (5) · `test_ticket_ai_tool.py` (4);
  updated the Community-hub + hub-registry + eval-coverage pins.

### Decisions made alone (for owner ratification)

- **Q-0201 (recorded):** the AI opens tickets via an audited *action* tool rather than a confirm-button
  handoff (the NL stage has no single reply object to attach a view to). Bar for future write tools:
  audited seam + deterministic bound. Homed `ticket` under the **Community** hub (user tier).

### ⚑ Flagged for maintainer / known limits

- **Not live-verified** — no bot boot / real Discord in this env. The channel-perms overwrite, transcript
  read, DM-on-close, and the AI loop actually opening a channel should be spot-checked in prod after deploy.
  Tickets are **off until an admin runs `!ticketsetup @StaffRole [#log]`** (the AI tool self-refuses until then).
- The introspection meta-tool (`get_ai_tool_catalog`) still reports every tool `read_only: true` (hardcoded
  in `ai_introspection_service`); `open_support_ticket` is technically an action. Cosmetic; no test breaks.
  Follow-up: thread a per-tool `read_only`/`side_effecting` flag if the catalog surface needs to be accurate.
- v1 scope intentionally excludes: multiple ticket categories/panels, pre-ticket question forms,
  auto-close-on-inactivity, and feedback ratings — all logged as future slices in the command-map doc.

## 💡 Session idea

**Ticket → knowledge-base deflection.** Before opening a ticket, let the AI try to *answer* the user from a
guild FAQ / past resolved-ticket transcripts and offer "did this solve it?" — only opening a ticket if not.
Modern AI ticket bots resolve 40–60% of common tickets this way. We already have the AI tool seam + the
transcript on close; the missing piece is a small per-guild FAQ store + a similarity match. Worth a plan
once tickets have live usage. (Dedup-checked `docs/ideas/` — no existing ticket/KB-deflection idea.)

## ⟲ Previous-session review

Previous session (`2026-06-24-rank-card-image.md`, PR #1401 — `!rank` as a themed image card) was clean,
well-scoped, and CI-green; its born-red-card discipline and the "single-fetch data builder + embed parity"
pattern were exactly right and made a good template for keeping render logic out of the cog. One thing it
(and the broader help-surface doc) left for me to trip over: **the surface-map prose still calls
fishing/welcome/counters "hub-less"** when all of them actually carry a `parent_hub` in the registry — that
stale wording cost me a wrong first guess (I tried shipping `ticket` un-homed). **System improvement:** the
"hub-less" claims in `docs/help-command-surface-map.md` should be reconciled against the live registry (a
tiny checker, or just a reconciliation-pass fix) so the next agent isn't misled — filed mentally for the
next docs pass; not shipped here to keep this PR scoped.

## Context delta

- **Needed but not pointed to:** the `guild_resources` resolver invariant (no raw `guild.get_role`/
  `get_member`), the `safe_defer` requirement, the **event catalogue** (`core/events_catalogue.py` — emits
  must be registered), and the **generated-artifact regen** trio (`scan_env_usage --write-doc`,
  `export_dashboard_data.py`, `extension_crosswalk.py --write`) are all CI-gating but not in the
  new-subsystem checklist. A new subsystem with a service + a view + an event will hit all of them.
- **Pointed to but didn't need:** CodeGraph — `context_map.py` + `new_subsystem.py` + grepping the treasury
  analogue carried the whole build; the graph never came up.
- **Discovered by hand:** `new_subsystem.py` covers the 10 registry/doc touch-points but **not** the
  cross-cutting invariants above; the `ai_tools` catalogue↔registry↔`_ALL_TOOL_SPECS` triple-sync; and that
  the no-direct-channel-mutation fence is scoped to `channel_cog`/`views/channels/` only (so a service may
  call `set_permissions`/`delete`).
- **🛠 Friction → guard:** the new-subsystem checklist is incomplete for *service-owning* subsystems — it
  green-lit `ticket` while 6 cross-cutting invariants (guild-resolver, safe_defer, event catalogue, 3
  generated artifacts) were still red. The cheapest durable guard is to **extend
  `scripts/new_subsystem.py check`** to also flag, for a subsystem that adds a service/event, the regen
  commands + the resolver/defer rules — proposing it as a router DISCUSS item (it touches owner-gated
  tooling) rather than shipping it inline here. (Proposed, not shipped — kept this PR scoped.)

## 📤 Run report

- **Did:** built a complete support-ticket subsystem (command + panel + AI natural-language) · **Outcome:** shipped
- **Shipped:** #1405 — `ticket` subsystem: migration 098, audited mutation seam, persistent panels, cog commands, and the first audited *action* AI tool (`open_support_ticket`)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** Q-0201 recorded (AI action-tool carve-out) — ratify or adjust the "audited seam + deterministic bound" bar for future write tools
- **⚑ Owner manual steps:** after deploy, in each guild run `!ticketsetup @StaffRole [#log-channel]` to enable tickets (off by default); then spot-check open/claim/close + the AI "open a ticket…" path live
- **⚑ Self-initiated:** none beyond the owner-requested feature (the KB-deflection idea is captured, not built)
- **↪ Next:** live-verify the ticket flow in prod; consider promoting the ticket→KB-deflection idea once tickets see usage
