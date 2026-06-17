# Session — generated-artifact freshness umbrella (one drift reporter for every committed generated file)

> **Status:** `in-progress`
> **Branch:** `claude/magical-rubin-w937u6`
> **Date:** 2026-06-17

## What I'm about to do

Scheduled DISPATCH fire, **empty work order**. Oriented: the buildable-now ungated `ready`
queue is genuinely thin (BTD6 deterministic-floor lane essentially exhausted — #1024 shipped the
two named candidates; moderation-DM shipped #1023; dashboard write/manifest lanes are owner-paced;
image-mod #941 + security #929 are Hermes-review carve-outs; phase gate = FIX). All three committed
generated artifacts verified **currently fresh** this run, so there is no *drift to fix* — but the
gap the #1025 session flagged is real and durable: each artifact is guarded in isolation and nothing
prevents the next silent rot.

**Building the freshest captured idea** — the
[generated-artifact freshness umbrella](../docs/ideas/generated-artifact-freshness-umbrella-2026-06-17.md)
(Q-0089 from #1025), as **Q-0105 dev tooling** (read-only · stdlib · warn-only · disposable, with the
mandated provenance header; NOT hard-CI-wired — ask-first): `scripts/check_generated_artifacts_fresh.py`,
a registry-driven umbrella over the three committed-and-generated artifact families —
`dashboard/data/dashboard.json` (delegates to the existing `check_dashboard_data --drift`),
`docs/operations/env-vars.md` (env-var name identity set), and `docs/agent/generated/*.context.md`
(line identity, date line dropped). Reuses each artifact's own generator; compares structural
identity only (never the volatile churn — line numbers, timestamps), the #1025 lesson. Tests +
mark the idea built.

> Born-red gate (Q-0133): flip to `complete` as the deliberate final step.
