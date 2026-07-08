# 2026-07-08 — EAP email + direction handoff doc

> **Status:** `complete`

**Scope:** owner-directed — this session is long (once-compacted); scan it for everything useful and
create a dedicated handoff so the **next direct session** can help direct the program + finalize the
Anthropic email with the owner. Docs-only.

## What shipped
- **`docs/planning/eap-email-and-direction-handoff-2026-07-08.md`** — the handoff: the next
  session's job, why it's a chat not a Project, what's LIVE (Task A running; both new repos
  bootstrapped via API; step 7 unblocked), the email's home + discipline, the full findings
  inventory (proven / strong-hypothesis / open), the owner's "purpose is overstated" critique
  captured precisely, the open decisions, durable pointers, and the working discipline.
- Discoverability pointer added to the top of the email doc
  (`projects-eap-activation-plan-2026-07-07.md`).

## Key reflections captured this session
- **Don't move management into a Project** — a coordinator is *more* constrained than a direct chat
  (no shell, 4 KB cap, can't orchestrate destructive even under a standing grant). Projects is an
  execution substrate, not a management console. → email point.
- **API bypass** (Contents API create/update/delete incl. workflows) makes the new-repo build ~90%
  agent-doable; only settings/secrets are owner-only.

## ⚑ Owner action / next
Next session starts from the handoff doc. Owner's open moves: send email 1; scope the new-repo
CI/tooling task; fold Task A's dedupe result into cell #1; set new-repo rulesets + `ROUTINE_PAT`.

## 💡 Session idea (Q-0089)
**"Management console vs. execution substrate" as a first-class evaluation axis** for the EAP —
name it explicitly in the eval log: does the product help *direct* the work or only *run* it? This
session found they're different surfaces with different tool constraints, and the distinction is the
sharpest single framing for the feedback. (Extends the product-review axes.)

## ⟲ Previous-session review (Q-0102)
The prior stretch (compaction-summary era) did well to keep every email edit tied to a verifiable
source — that discipline is why the email survived two rewrites without drift. What it could have
done better, and this session fixed: it treated the permission wall as a hard blocker ("blocks the
rebuild"); the honest reframe is *friction, not a work-stopper* + the API workaround. System
improvement: the handoff-doc pattern itself — a long session should end by distilling state for its
successor, not just a session card.

## ⚑ Self-initiated
Owner-directed handoff; no unprompted scope.
