# 2026-06-24 — Tickets: setup-wizard discoverability

> **Status:** `in-progress` — wiring tickets into the `!setup` wizard + bot-join launcher so a new server
> owner discovers tickets exist and need `!ticketsetup`. (Born-red card; flipped to `complete` as the last step.)

> **Run type:** `manual` — owner asked "how easy is it for owners to discover this setup?", then said continue.

**Branch:** `claude/ticket-setup-discoverability` (off `main`). Follows the ticket subsystem (#1405) + AI
confirm rework (#1410). A discoverability audit found tickets are reachable via `!help` → Community hub, but
**absent from the `!setup` wizard and the bot-join welcome** — the surfaces a new owner actually hits first.

## What this session is doing

- **New `views/setup/sections/ticket.py`** — a setup-wizard section so tickets appear in `!setup` / `/setup-hub`.
  Direct-lane config panel (RoleSelect staff role + ChannelSelect log + Enable) writing through the audited
  `ticket_mutation.update_config` — the same path `!ticketsetup` uses. Tickets store config in their own
  table (not the generic `set_setting` pipeline), so it stages no draft ops (like `suggestions`/`server_scan`).
- **Launcher mention** — a line in the bot-join welcome embed pointing at the Support Tickets step / `!ticketsetup`.
- Tests + the section-registration pin updated.

(close-out notes appended at session end)
