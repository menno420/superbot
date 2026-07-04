# 2026-07-02 — Harden the new-bot capability-audit BRIEF (prompt-refinement pass)

> **Status:** `complete`
> **Branch:** `claude/review-recent-session-qcyc44` · **PR:** (opening)
> **Session type:** follow-up — apply the owner's GPT prompt-refinement suggestions to the shared contract

## What happened

The owner ran the fleet handoff prompts through a GPT prompt-engineering project; it returned refined
per-session prompts + suggested shared-contract edits. Verified the refinements against source (Q-0120):
all 14 read-paths the prompts reference exist. Applied the four genuinely-good shared edits to
`BRIEF.md` **once** (they propagate to every lane, since all read BRIEF first) rather than duplicating
them into each prompt:

- **Substrate precondition** — confirm the contract files exist (on `main` via #1661); report if missing,
  don't invent the schema.
- **Documentation-only boundary** — the precise allowed-writes rule (assigned audit md + findings +
  session/PR metadata; no `disbot/`, tests, migrations, configs, generated, or new-repo code).
- **Capstone carry-forward fields** — every recommendation carries dependency-layer · done-definition ·
  outperform-target · owner-gated status (the capstone can't order the build plan without them).
- **Phase-3 hard stop** — the rebuild is owner-gated; the audit is planning evidence, not build approval.

Added a `HANDOFF-PROMPTS.md` header pointer so a repo-launcher knows the preconditions live in BRIEF.
Docs-only; read-only; no runtime code.

## ⚑ Self-initiated

None beyond the owner's direction — applied the owner-relayed GPT suggestions after verifying them.

## 💡 Session idea

**Fold the "launch preconditions" block into the substrate-kit templates.** The four guards added here
(substrate check · docs-only boundary · carry-forward fields · owner-gate hard stop) are generic to *any*
multi-agent audit contract, not just this one — a good addition to the `/fleet-audit` skill idea captured
last session, as the default contract header. Dedup: extends the prior fleet-substrate idea, doesn't duplicate.

## ⟲ Previous-session review

The previous session (the audit-substrate prep) correctly put the shared contract in one `BRIEF.md` that
every lane reads — which is exactly why this hardening was a **one-file** change instead of editing seven
prompts. That "one shared contract" decision paid off immediately. No miss to flag; the design held.

## 📊 Telemetry

- new-bot-capability-audit BRIEF hardened with 4 launch-precondition/boundary guards (verified vs source)
- Docs-only; `check_docs --strict` green; zero runtime code
