# Session — EAP email refresh + forward-only Project instructions

> **Status:** `complete`

## What this session did
Owner-directed management/chat session (continues the EAP-feedback thread). Docs-only. Delivered:

1. **Refreshed the Anthropic EAP feedback email** into a consolidated, send-ready standalone doc —
   `docs/planning/projects-eap-anthropic-email-2026-07-08.md`. New this refresh:
   - Folds in the owner's new finding: the claude.ai **Chat/Cowork "Skip all approvals"** toggle
     enables even destructive actions, while Claude Code Projects auto mode has **no scoped
     equivalent** and walls destructive git even when prompted. Made the **value anchor** — our ask
     (scoped, opt-in, default-off pre-auth) is *strictly safer* than a blanket toggle Anthropic
     already ships in Chat.
   - Restructured to the shape the owner asked for: **Positives / Negatives / What-we-tried-and-why /
     Why-the-ask-is-valuable / explicit Asks-back** (test cases they'd like run · settings/workarounds
     we may have missed · is-this-intentional-do-you-want-to-keep-it · Contents-API-vs-git-push
     asymmetry).
   - Every claim tied to a source (verifiability appendix table). Marked the "Projects can't replace
     direct management" paragraph **⚑ owner-review: keep/soften/cut**.
2. **Forward-only Project custom instructions** —
   `docs/planning/forward-only-project-custom-instructions-2026-07-08.md`: ready-to-paste block for a
   fresh Project scoped so agents never *attempt* a destructive/prompt-forcing action, plus the
   forward-only equivalence table and owner setup notes. This is the setup half of the forward-only
   quality experiment.
3. **Wiring:** forward-only idea doc → points at the instructions (status: setup shipped, awaiting
   run); activation-plan §4 → points at the new canonical email doc; handoff brief → email pointer
   retargeted; evaluation log → new lived entry for the Chat/Code "Skip all approvals" asymmetry.

PR #1853 (docs-only). `check_docs --strict` green.

## ⚑ Self-initiated
None beyond the owner-directed scope. (Idea file added per Q-0089 ender; not a self-promoted build.)

## Open for the owner (decide-and-flag)
- **Send the email** — recommended as the single substantive note now (not interim-then-full); the
  Skip-all-approvals precedent + explicit asks make it worth leading with. External comms are yours.
- **The "can't replace direct management" paragraph** — keep / soften / cut before sending.
- **Fresh vs. re-instruct** for the forward-only Project — you asked for fresh (cleaner A/B); block
  pastes into either.

## 💡 Session idea (Q-0089)
`docs/ideas/session-start-capability-self-probe-2026-07-08.md` — a cheap read-only session-start
self-probe recording which tools a session actually has (shell / git write / self-wake / spawn types),
so protocols premised on a missing tool (the standing-grant `NOT ATTEMPTED` row; phantom `send_later`)
fail free-and-early instead of late-and-expensive. The self-serve version of the email's spawn-time
capability-introspection ask. Dedup-checked against the probe report and the staleness-banner idea.

## ⟲ Previous-session review (Q-0102)
Previous session (`2026-07-08-eap-direction-handoff.md`) did the hard, right thing: it wrote a genuine
handoff brief so a fresh session (this one) could pick up the email+direction role cold — and it did,
with near-zero re-derivation. It also made the correct *product* call (keep management in a direct
chat, not a Project) with a clear rationale. **What it could have done better:** it left the email
split across two homes (§4 draft + a chat-only "polished draft") with no single canonical file, which
forced this session to consolidate; a handoff that names *one* send-from file is cheaper for the next
session. **System improvement surfaced:** the recurring EAP pattern is "a finding lives only in chat
or a screenshot" (the Skip-all-approvals toggle came in as an image). The capability-self-probe idea
above is one guard; a lighter complementary one is a standing convention that *every* external-product
observation gets a one-line evaluation-log entry the same session it's seen — so the email always
assembles from the log, never from scrollback.

## 📋 Doc audit (Q-0104)
`check_docs --strict` green (new docs reachable, badges valid). No ledger entry needed yet — PR #1853
is unmerged; the living-ledger checker covers it on merge. New owner-facing decisions here are
reversible/flagged, not router-worthy (no new binding rule). Nothing from this session lives only in
chat: the email, the instructions, the new finding, and the idea all have durable homes.
