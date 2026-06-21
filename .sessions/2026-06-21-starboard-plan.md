# 2026-06-21 — Starboard / Hall-of-Fame: buildable plan

> **Status:** `complete` — docs-only (plan). **⚑ Self-initiated** (Q-0172): backlog-grooming after the
> reaction-roles arc completed. Pushed all-at-once before opening the PR (CI-refire gotcha). Q-0191 →
> merge on green.

> **Run type:** `manual`

## Arc

The reaction-roles arc is fully shipped + merged (#1234/#1237/#1243/#1246/#1248/#1250) and its lessons
captured (#1253). Per the standing "main task done → advance the backlog" rule (Q-0015 grooming +
Q-0172 idea→plan→build), I promoted the **highest-value, lowest-risk captured idea that builds on what
I just shipped**: **Starboard** (idea B1). The reaction-roles plan §6 explicitly named it the next
Carl-parity item *because it reuses the raw-reaction seam I just hardened*.

Wrote `docs/planning/starboard-plan-2026-06-21.md` — a complete, buildable spec: schema
(`starboard_settings` + `starboard_entries`), the layering that mirrors the reaction-role seam exactly
(`utils/db/starboard` → audited `starboard_service` → `starboard_cog` raw-reaction listener), the
behaviour rules that make it "low risk" (recount-don't-increment, self-star, threshold-cross
post/edit/delete, dedupe via PK, don't-starboard-the-starboard), the arch checklist, and a 2-PR
breakdown. Registered it in the planning index (S1).

## Findings / decisions

- **Decision made alone — plan, don't full-build, this turn.** Starboard is a new *subsystem*
  (migration + DB + service + cog + listener + wiring). Grooming says structure a bigger idea into a
  plan; a full subsystem built fully autonomously on a generic "continue" — with live migration-number
  coordination against other active sessions — is a big unprompted swing with real bug surface. A
  complete, buildable plan is the disciplined, low-risk, high-value step, and it makes the build a
  clean focused session (PR 1 ships a working v1).
- **Reuse over reinvent:** the plan deliberately mirrors `reaction_role_service` (audited seam,
  raw-reaction guards, guild teardown) so the build is pattern-for-pattern with code I just wrote.

## 📤 Run report

- **Did:** promoted idea B1 → a buildable starboard plan; registered it in the planning index ·
  **Outcome:** shipped (docs-only PR, auto-merge on green)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** one small open Q in the plan (§8: fixed ⭐ vs configurable emoji for
  v1 — build can proceed either way). Greenlight to **build PR 1** whenever (or redirect).
- **⚑ Owner manual steps:** none — merged = deployed (docs change, nothing to deploy).
- **⚑ Self-initiated:** YES — backlog grooming (idea→plan) after the owner's reaction-roles work was
  fully delivered.
- **↪ Next:** build **starboard PR 1** (foundation + working v1) — it's spec'd and reuses the
  hardened seam; or the owner points me at a different priority.

## 💡 Session idea

**A `/plan-status` digest** that lists `docs/planning/` Active plans with their badge + "▶ buildable /
gated / in-flight" state, so "what's the next buildable thing?" is one command instead of reading the
index + cross-checking `current-state.md`. The planning README is good but static; a generated digest
(reuse the badge parser from `check_docs`) would make backlog grooming — the exact thing this session
did by hand — a one-liner. (Dedup-checked `docs/ideas/` — the closest is the agent-tooling shortlist,
which doesn't cover a plan-status view.)

## ⟲ Previous-session review

The chain's prior sessions (mine) shipped 6 reaction-roles PRs well, but I twice *handed the wheel
back* ("pick a direction") when the repo's own standing rule (Q-0015/Q-0172) already answers "what to
do when the main task is done": **groom the backlog and advance an idea.** **System improvement:** an
agent shouldn't stall on "what next?" when the explicit task is complete — the backlog + the grooming
rule *are* the next thing. This session applied that instead of asking again.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (pending docs PR, auto-merge on green) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`/plan-status` digest) |
| Ideas groomed | 1 (promoted B1 Starboard → a buildable plan) |
