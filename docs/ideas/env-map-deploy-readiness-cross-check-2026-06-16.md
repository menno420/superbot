# Idea — turn the env-usage map into a deploy-readiness check (required-but-unset detection)

> **Status:** `ideas` — captured 2026-06-16 (Q-0089 session ender, from the dashboard Phase 3
> env-usage map #969). Builds directly on the just-shipped `scripts/scan_env_usage.py`. Area:
> dashboard / operations (the Phase 3 secrets zone).

## The seed

`scripts/scan_env_usage.py` (#969) now knows, statically and authoritatively, **which env vars the
bot requires** (read without a default — currently `DATABASE_URL`, `DISCORD_BOT_TOKEN_PRODUCTION`,
`YOUTUBE_API_KEY`). That is exactly the input a *deploy-readiness* check needs: a deploy is
misconfigured the moment a **required** variable is unset, and today nothing surfaces that until the
bot crash-loops on boot (the `DATABASE_URL ... is required` raise) or a feature silently degrades.

## The idea

When the dashboard's Phase 3 **Railway-backed value management** lands (the half gated behind owner
login + the Railway API), cross-reference the scanner's `required: true` set against the **names
present** in the target Railway service's variables (names only — never values). The `/env` page
then renders each required var as ✅ *set* / ❌ *missing*, and a single top-line
**"deploy-ready / N required variables unset"** banner. The optional vars get a softer "set / using
default" badge.

Pure name-level comparison: `scan_env_usage()` gives the required-name set; the Railway API gives
the present-name set; the dashboard diffs them. No secret value is ever read, stored, or rendered —
consistent with the #969 safety guarantee and the plan's "no second vault" principle.

## Why it's worth having

- It converts a passive *inventory* into an active *check* — the difference between "here are the
  vars" and "your deploy is missing one." That is the owner's original ask ("safely store env
  values and **track where each is used**") taken one useful step further: track whether each
  *required* one is actually provided.
- It catches the highest-severity, easiest-to-make config error (a forgotten required secret on a
  fresh service / a renamed Railway variable) before it reaches a crash-loop — and it does so with
  data the scanner already produces, so the marginal cost is a name-set diff and a badge.

## Sequencing

Gated on the Phase 3 Railway-API integration (owner login + `RAILWAY_API_TOKEN` scope, already
documented in `production-deployment.md` Q-0130). Until then the static half is shippable: the
scanner can already emit the required-name list as a deploy checklist (`--write-doc` surfaces it),
and the live cross-check rides on the authenticated Railway read when that lands.
