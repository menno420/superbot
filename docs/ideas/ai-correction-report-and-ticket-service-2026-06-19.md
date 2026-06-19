# AI reports corrections → an audience-routed AI ticket service

> **Status:** `ideas` — **owner-directed (2026-06-19, brainstorm). NEEDS ITS OWN EXTENSIVE SESSION —
> capture only, not a plan.** Source + the binding contracts win.
> **Subsystem:** ai — the AI's first write/report capability.

## The owner's framing (verbatim intent)

> *"it should slightly remember stuff about users but not too much to prevent high API costs … it should
> be able to post on the website as well, like if a user corrects it on something, all it does now is
> either deny or acknowledge it, but the best thing would be if the AI could actually report this to us,
> and this would also be a good first step towards the AI ticket service, that allows users to send in bug
> reports, server problems, moderation things etc. This should be its own extensive session later because
> it must account for many things, like for who is the report meant, what is the correct response etc, we
> can't have the AI accidentally send a server bug to the bot website."*

## The seed (near-term) and the vision (later)

- **Seed:** today, when a user corrects the AI, it can only *deny or acknowledge*. Instead, let the AI
  **file the correction for the owner to review** — a write into the **owner review inbox**, never the
  public site.
- **Vision:** an **AI ticket service** — users send **bug reports · server problems · moderation issues**
  *through the AI*, which triages and routes each to the right audience.

## The hard part (owner-named): audience routing, fail-closed

The central problem is **not** "can the AI write a ticket" — the rails for that mostly exist (below). It is:

> **Can the AI correctly classify *who each report is for* — owner-private · this server's mods · the
> public bug tracker — with a guard that fails closed so a server-private issue can NEVER leak onto the
> public website?**

When the classifier is unsure, the safe default is **owner-private, never public**. This is the same
audience/redaction discipline the website split already enforces by construction (the `site.json`
fail-closed whitelist) — the ticket router needs an equivalent, applied to *outbound* reports.

## Existing rails (don't rebuild these)

- **Owner review inbox** — the `/reviews` board (Phase 1 shipped #1091);
  [owner-review-inbox-plan](../planning/owner-review-inbox-plan-2026-06-17.md). *The near-term write target.*
- **Website submissions DB + moderation pipeline + GitHub-issue mirror** (website split) — the public
  intake path the ticket service would *route to* only after an explicit human approve step.
- [per-command-feedback-threads](./per-command-feedback-threads-2026-06-19.md) — AI-moderated per-command
  feedback; the same moderation/store the ticket service reuses.
- [hermes-bug-triage-flow](./hermes-bug-triage-flow-2026-06-13.md) (Q-0121) — the triage→curated-issue
  mechanism; the ticket service is its user-facing front door.

## Why it is gated / design-first (correct, not over-caution)

- This is the AI's **first real write / external capability.** Per the standing **Q-0048** posture,
  read-only AI ships freely but **writes/external calls need a per-exposure design + lift** — so a careful,
  dedicated session is the *rule*, not timidity.
- **Memory stays light** (owner: keep it small to control API cost) — conclusion-style, opt-in, bounded
  under the **Q-0082** spend ceiling. Memory is a *companion* feature; the reporting/ticket capability is
  separate and the higher-stakes one.

## What the dedicated session must define (checklist for later)

- The **report schema** (kind: correction / bug / server-problem / moderation; subject; evidence).
- The **audience classifier** + its **fail-closed default** (unsure → owner-private; never auto-public).
- **Redaction** — a server's private detail must never cross into a public/GitHub artifact.
- A mandatory **human approve step** before any report becomes public or a GitHub issue.
- **Dedup** ("was this already reported?") and **abuse/cost controls** (stranger-grade, Q-0080/Q-0082).
- The **"correct response"** back to the reporting user (acknowledge · "filed for review" · resolution).

→ relates [owner-review-inbox-plan](../planning/owner-review-inbox-plan-2026-06-17.md) ·
[per-command-feedback-threads](./per-command-feedback-threads-2026-06-19.md) ·
[hermes-bug-triage-flow](./hermes-bug-triage-flow-2026-06-13.md) · the website-split redaction contract ·
the [ai folio](../subsystems/ai.md) · Q-0048 (AI write gate) · Q-0121 (Hermes triage write scope).
