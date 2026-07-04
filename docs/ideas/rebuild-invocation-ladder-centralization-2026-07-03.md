# Idea — the invocation-stack centralization set (C-1…C-7)

> **Status:** `ideas` — capture only (proposals pending owner reaction, recorded as Q-0228).
> **Subsystem:** none (rebuild interaction runtime / command stack). **Provenance:** Phase-A
> conventions-freeze session (PR #1680), from the owner's "what else could we centralize?" prompt.

## The idea

Applying the second-consumer rule (Q-0219) to the command/invocation area surfaces seven things
worth collapsing into single engines rather than per-command/per-rung copies:

- **C-1 — one command resolver** all four invocation rungs funnel through (authority + arg
  validation/coercion + cooldown + audit → run). *The convergence point — strongest recommend;*
  without it every rung re-implements auth/validation and they drift.
- **C-2 — one preview/confirm/apply (draft) pipeline, two producers** (AI drafts, fuzzy-corrected
  destructive actions, NL actions, human setup all share it).
- **C-3 — one template primitive** (named reusable draft, human- or AI-instantiated; unifies the
  scattered setup/role/channel templates; serves the "10 D&D channels" example).
- **C-4 — one response/result grammar** (`WorkflowResult` — consistent success/failure/denial;
  the silent-vs-reply decision in one place).
- **C-5 — one fuzzy/"did-you-mean" engine** (fold the scattered `difflib` uses in setup advisor /
  presets / recommenders into the typo rung + suggestion renderer).
- **C-6 — one cooldown/rate-limit engine** (per-user/guild/command; the free-for-everyone abuse
  posture's natural home).
- **C-7 — one description surface** feeding slash help, help projection, the NL router intent
  surface, the fuzzy candidate set, and "did you mean" — write each command's description once.

## Why it's worth having

The invocation ladder has four front-ends; if each re-implements resolution, confirmation,
cooldowns, or suggestions, the rebuild recreates exactly the scattered-logic problem it exists to
kill — and inconsistency in *auth/validation* specifically is a safety bug, not just untidiness.
Collapsing to single engines is the generalization standard applied where it has the most consumers.

## Routing

Full detail + agent recommendations in
[`../planning/rebuild-conventions-invocation-authority-2026-07-03.md`](../planning/rebuild-conventions-invocation-authority-2026-07-03.md)
§6. Owner reacts (Q-0228); blessed items become Gate-0 (K8 interaction runtime) / Phase-B
contracts. Not current-repo work.
