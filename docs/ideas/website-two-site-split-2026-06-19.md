# Idea: split the dashboard into two audience-targeted sites

> **Status:** `ideas` — capture. **Owner-directed (2026-06-19), decisions in router Q-0178; structured
> into a planning brief.** Source code + binding contracts win. Not the plan — the plan is the next
> session's job (see the brief).
> **Subsystem:** none — the dashboard/website split (infra, not a bot subsystem).

## The idea

Split the single developer dashboard (`dashboard/`) into **two sites by audience**:

- **Bot site (public, dynamic):** for Discord users — command reference, feature showcase, bot
  changelog/updates, status, and a **public bug/suggestion form**.
- **Dev/repo site:** the current dashboard, repurposed — ideas, bugs, repo/session updates, env map,
  `/reviews`, control plane. **All pages public read-only**, owner-gated for edits.

Submissions flow **DB → owner approves → mirror to GitHub issues**; deployed as **2 Railway services**
(repurpose the dashboard + a new bot site). Rationale: bot-users and dev/ops content have different needs;
separating them sharpens both.

## Why it's worth having

A clean public bot site is a real user-onboarding upgrade, and the dev dashboard stays the unpolluted
"engine room." Feasible because `dashboard/` is already a decoupled Railway service reading generated JSON.

## Route

**Owner-directed → structured** into
[`planning/website-two-site-split-planning-brief-2026-06-19.md`](../planning/website-two-site-split-planning-brief-2026-06-19.md)
(the required output for the next planning session). Decisions: router Q-0178.
