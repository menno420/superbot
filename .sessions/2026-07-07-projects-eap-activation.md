# 2026-07-07 — Claude Code Projects EAP: access granted, activation window

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only (no
> `disbot/` runtime code): `check_docs.py --strict` and `check_current_state_ledger.py --strict`
> both green (ledger note = benign newest-merge lag, #1804/#1805).

## What's new since #1776/#1777

Prior session (`2026-07-07-projects-eap-and-full-autonomy-q0241.md`, PR #1776) evaluated the
**invite** PDF and wrote `docs/ideas/claude-code-projects-for-the-rebuild-2026-07-07.md` +
`docs/planning/projects-eap-product-review-2026-07-07.md` speculatively. Owner-supplied email
thread (Omid → Diana, forwarded 2026-07-07) confirms: **access is now enabled**, and per Diana's
reply, **CC Projects is free only through Friday 7/10** — a 3-day activation window, not an
open-ended one. This session turns the prior analysis into an actual activation plan for that
window (still docs-only; standing up the Project itself is an owner-side UI action at
claude.ai/code/projects/browse, not something this session can do).

See `docs/planning/projects-eap-activation-plan-2026-07-07.md` for the plan, rubric, and
feedback-reply draft.

## ⚑ Self-initiated

None — this session's scope was the owner's own message (forwarded EAP access email + explicit
ask to brainstorm use case / review approach / Anthropic feedback). No promotions beyond that ask.

## 💡 Session idea (Q-0089)

**Trial-window tripwire.** The activation plan's 3-day window (free through Fri 7/10) is exactly
the kind of externally-imposed deadline that's easy to let slip once a session ends. Idea: a
`send_later`/routine self check-in timed to the deadline itself (not just the usual hourly PR
babysit) that re-surfaces "did the §3 rubric get run, did the §4 reply get sent" if nobody has
acted by then — a generic pattern for any EAP/trial/offer with a hard external clock, not just
this one. (Grep-checked `docs/ideas/` — not present as a general pattern.)

## ⟲ Previous-session review (Q-0102)

Previous distinct session (#1776, the EAP-invite eval + Q-0241): **did well** — it correctly
separated the durable governance change (Q-0241, its own provenance) from the speculative product
idea, so today's follow-up could cleanly extend the idea doc rather than re-litigate the rule.
**Could have anticipated:** it framed activation as a single "owner accepts the invite" gate
without noting that EAP access, once granted, often carries its own clock (a free-trial window) —
that's exactly what showed up today and reshaped the plan from "scope broadly" to "one bounded
stream, 3 days." **System delta:** worth a standing habit — when a speculative idea doc names an
external dependency (an invite, an API waitlist, a partner offer), flag in the doc itself that
acceptance may arrive with a deadline, so the follow-up session isn't the first one to notice.

## ▶ Next action

Owner-facing (§5 of the activation plan): create the Project, paste Custom Instructions, run it
against the kit-lab or next port-band, score the §3 rubric, send the §4 reply before Fri 7/10.
