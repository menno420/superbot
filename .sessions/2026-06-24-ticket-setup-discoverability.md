# 2026-06-24 — Tickets: setup-wizard discoverability

> **Status:** `complete` — tickets now appear in the `!setup` wizard + the bot-join welcome. Full CI mirror
> green (12390 passed); arch 0 errors. Shipped as PR #1417.

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

### ⚑ Flagged for maintainer / known limits

- **Not live-verified** (no Discord boot here): confirm tickets show up in `!setup` (standard/advanced
  depth) and `/setup-hub`, the panel's RoleSelect + ChannelSelect + Enable flow writes config, and the
  bot-join welcome shows the new line. The Enable path reuses the audited `update_config` that
  `!ticketsetup` already exercises, so the write seam is the proven one.
- The section is **standard + advanced** depth (not `quick`) — tickets aren't a day-one essential. Reasonable
  default; flag if you'd rather they appear in the quick path too.

## 💡 Session idea

**Readiness scan should grade tickets.** The setup readiness scan (`build_setup_readiness_embed`) rates how
configured a server is, but doesn't know about tickets yet. Adding a "🎫 Tickets: enabled / not set up" line
would both grade them and act as another discovery nudge. Small, follows the existing readiness-row pattern.

## ⟲ Previous-session review

The previous two sessions (#1405, #1410) built the ticket subsystem and AI flow well, but **both declared
the feature "done" while it was effectively undiscoverable through the wizard** — the gap this session
found only because the owner asked. Lesson: "shipped" for a user-facing subsystem should include *how a
user finds it*, not just that the code works. **System improvement:** the `new-subsystem` skill / subsystem
registry could carry a checklist item — "is this wired into `!setup` and the launcher?" — so a new
subsystem can't be marked complete while invisible to the setup flow. Captured as the session idea's cousin;
worth a router note if it recurs.

## Context delta

- **Needed but not pointed to:** the rule that a setup section can write **directly** (not draft-staged)
  when its domain owns a dedicated audited mutation — `suggestions`/`server_scan` model it, but it isn't
  spelled out in the setup-section docs. Worth a one-liner in the section-authoring guide.
- **🛠 Friction → guard:** none new — `check_quality.py --full` + the section-registration pin caught
  everything; the moderation section was a clean template.

## 📤 Run report

- **Did:** wired tickets into the `!setup` wizard + bot-join welcome · **Outcome:** shipped
- **Shipped:** #1417 — tickets discoverable via `!setup` / `/setup-hub` + the welcome embed
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** after deploy, spot-check tickets appear in `!setup` and the panel enables them
- **⚑ Self-initiated:** none — owner asked the discoverability question, then said continue (directed work)
- **↪ Next:** live-verify; optionally the "readiness scan grades tickets" idea
