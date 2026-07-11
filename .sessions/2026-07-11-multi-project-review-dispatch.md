# 2026-07-11 — Multi-project review + fleet centralization plan + dispatch kit

> **Status:** `in-progress`

📊 Model: Opus 4.8 · owner-directed hub session (fleet management / planning + triage) · ultracode

## What I'm about to do (born-red hold)

Owner-directed continuation of global fleet management. Deliverables (docs-only, landing
on this branch's PR for the owner to gate):

1. **Full-fleet review** — verified scan of all 19 repos (15 active) via a parallel
   discovery fan-out: state, products, errors/arch-violations, drift, centralization.
2. **Codex-review verification** — verify the 4 dispatched Codex reports (superbot-next,
   venture-lab, superbot-mineverse, substrate-kit) + any Codex PRs against source (Q-0120).
3. **Fleet triage register** — keep / replace / repurpose / delete verdict per repo &
   product (seeds the handoff's `fleet-triage.md` idea).
4. **Centralization plan** — fleet-manager as the single source of truth for cross-repo
   doc records via timely triggers; what moves there, and how it stays reachable.
5. **Dispatch kit** — 7 ready-to-fire session prompts (2× ChatGPT 5.6 Sol, 2× Codex
   [superbot + superbot-next], 1× Sonnet 5 ultracode, 1× fleet-manager) with correct
   permissions + known-problem workarounds baked in from the start.

Baking-in source (durable findings from the night review + handoff): `add_repo`
"[Unauthorized Persistence]" denials → attach repo to routine; no-PR-tooling in wake
sessions; model config-vs-actual mismatch; live-human-context-is-permission; project-scoped
Railway tokens; pytest-must-be-required-check.
