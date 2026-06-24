# 2026-06-24 — Ticket AI open: one-click confirm (follow-up to #1405)

> **Status:** `complete` — the AI `open_support_ticket` tool now proposes a ticket with a one-click
> [Open ticket]/[Cancel] confirm instead of opening directly (owner choice). Full CI mirror green + arch 0.

> **Run type:** `manual` — owner answered the open-flow question (AskUserQuestion) after #1405 merged.

**Branch:** `claude/ticket-ai-confirm-button` (off `main`, which now has #1405). **Trigger:** after the
ticket subsystem merged (#1405, AI-opens-directly), the owner picked **"one-click confirm button"** for the
AI open flow — the AI should propose, the user commits.

## What shipped (PR #pending)

Reworked the natural-language open path so the AI **never opens a ticket on its own**:

- **`services/ai_tools.py`** — `open_support_ticket` is now effectively read-only: it validates eligibility
  (`check_open_eligibility`) and, when allowed, emits `ticket.open_requested`; it creates nothing. Returns
  `{requested: true/false, reason, ...}`. Module docstring reverted from "the one action tool" to "no tool
  here mutates state". Factory gains `channel` (to address the confirm).
- **`core/events_catalogue.py`** — new `ticket.open_requested` event.
- **`views/tickets/confirm.py`** — `TicketConfirmView` ([Open ticket]/[Cancel], locked to the requester,
  120s) + `build_confirm_embed`. The Open button runs the audited `ticket_mutation.open_ticket(source="ai")`.
- **`cogs/ticket_cog.py`** — subscribes to `ticket.open_requested` and posts the confirm panel into the
  channel, addressed to the requesting member.
- Docs: Q-0201 reframed (confirm-gated, not an action tool), `ownership.md` event + AI-path note,
  eval-coverage ack reason.
- Tests: `test_ticket_ai_tool.py` rewritten — offering gate, refuses empty subject / ineligible without
  emitting, and **requests confirmation without opening** (asserts `open_ticket` is never called).

The command + panel-button open paths from #1405 are unchanged (they already required a human action).

### Decisions made alone (for owner ratification)

- The confirm seam reuses the same EventBus pattern as `ticket.opened` (service emits → cog posts UI),
  because a service must not import views. This keeps `ai_tools.py` free of any write and restores its
  read-only invariant — arguably cleaner than the #1405 first pass. Recorded in Q-0201.

### ⚑ Flagged for maintainer / known limits

- **Not live-verified** (no Discord boot here): confirm the AI "open a ticket…" path posts the button, the
  click opens the channel, and the requester-lock works. Tickets still need `!ticketsetup` first.
- The confirm view is transient (120s, non-persistent) — if the bot restarts between propose and click, the
  button goes dead and the user re-asks. Acceptable for a confirm prompt; persistence would be over-engineering.

## 💡 Session idea

**Confirm-then-collect.** The confirm button could open a short modal (one or two fields — e.g. priority, or
"anything else?") before creating the ticket, giving staff context from message one (the "ticket steps" the
best bots use). Small extension of the existing modal + confirm seam. Captured for a later slice.

## ⟲ Previous-session review

Previous session (this same feature, #1405) shipped the whole subsystem end-to-end and green, which was the
right call — but it **made the AI-open-flow decision unilaterally** (direct-open) when it was genuinely the
owner's to make; asking via AskUserQuestion *before* merge would have avoided shipping a design the owner
then changed. Lesson reinforced: for a user-facing interaction model with two reasonable options, surface
the choice early. **System improvement:** none beyond that judgment note — the workflow itself (born-red
card, auto-merge, the event-seam pattern) worked well and made this follow-up cheap.

## Context delta

- **Needed but not pointed to:** that a service-layer AI-tool handler can drive UI only via the EventBus
  (services can't import views) — the same seam `ticket.opened` already used. Worth noting in the AI-tools
  folio: "an AI tool that needs to show UI emits an event; a cog posts it."
- **🛠 Friction → guard:** none new — the rework was a clean diff on top of #1405.

## 📤 Run report

- **Did:** reworked the AI ticket-open to a one-click confirm (owner's choice) · **Outcome:** shipped
- **Shipped:** #pending — AI proposes a ticket via [Open ticket]/[Cancel]; the open is the user's click
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none — Q-0201 updated to record the confirm-button choice
- **⚑ Owner manual steps:** after deploy, spot-check the AI "open a ticket…" → confirm → channel-created flow live
- **⚑ Self-initiated:** none (owner-directed change)
- **↪ Next:** live-verify; optionally the "confirm-then-collect" modal idea once tickets see use
