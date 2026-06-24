# 2026-06-24 — Support-ticket subsystem (command + AI natural language)

> **Status:** `in-progress` — building a new support-ticket subsystem. Born-red card; flips to
> `complete` as the deliberate final step once the full CI mirror is green + arch 0 (Q-0133).

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

## What shipped (PR #pending)

_(filled in at session close)_
