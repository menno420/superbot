# 2026-07-02 — Railway: the full-automation grant (Q-0213) + R-now execution

> **Status:** `in-progress` — born-red (Q-0133). Run type: manual · owner-directed.
> Scope: record the owner's automation directive (router Q-0213), re-scope the Q-0130 Railway
> envelope, **execute the safe R-now hygiene items live via the Railway API** (each contained,
> reversible, read-back-verified; destructive ops stay ask-first), update plan/ops docs.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1638 merged).

## What I'm about to do (intentions)

The owner directed (in-chat, 2026-07-02): the full-access Railway account token is **deliberate** —
Claude is its sole holder and the repo's main editor; test-bot token + provider API keys are
likewise provided so **the whole project can be completely automated** without relying on the owner
to enter values or create workers. This supersedes the custody recommendation (declined) and
re-scopes Q-0130. Plan:

1. Record **Q-0213** in the question router; update the Q-0130 envelope in
   `production-deployment.md`; mark plan §7 decisions 1/3 decided.
2. Execute, with per-change read-back verification: **R2** backup schedules (daily+weekly+monthly)
   on the Postgres volume · **R1** wait-for-CI on the three deploy triggers (after verifying which
   checks run on `main` pushes) · **R4** botsite healthcheck (`/healthz` exists at
   `botsite/app.py:97`) · **R3** watch paths for dashboard+botsite only (worker stays
   deploy-on-everything — under-deploying the bot is the dangerous direction) · **R5** usage
   alert if the API exposes an alert-only threshold (a hard kill-limit stays an owner call).
3. Document the executed state; the standing safety brake is unchanged: no `*Delete`/`*Restore`/
   data-destructive mutation is ever run without an explicit owner ask.
