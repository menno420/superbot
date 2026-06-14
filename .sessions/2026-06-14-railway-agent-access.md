# 2026-06-14 — Railway agent-access + permission-autonomy (owner-directed, manual)

**Type:** manual, owner-directed (mobile, conversational). Diverged from the P0 spine by
explicit request — pure ops / access / workflow. Seven PRs, all auto-merged.

## What shipped (all merged)
- **#827 (Q-0128)** — `.claude/settings.json` → `defaultMode: bypassPermissions`, `ask: []`,
  `skipDangerousModePermissionPrompt: true`. Root cause: routines stalled on confirmation
  prompts (notably `git reset --hard`, which was in the `ask` list) in unattended sessions.
  No prompts now in any *fresh* session/routine.
- **#828 (Q-0129)** — autonomy stance made explicit (CLAUDE.md "Act vs ask" +
  `collaboration-model.md` §"Why this system exists"): unattended self-initiated
  workflow-improving action is *welcomed*. Plus the `send_later` journal note (not provisioned
  here — skip it; use subscribe+report + a git-ancestor Monitor).
- **#831** — `docs/ideas/routine-activity-visibility-2026-06-14.md` (routine runs hidden from
  Recents; DIY = Discord webhook ping; upstream FR anthropics/claude-code#54517).
- **#832 (Q-0130 T0)** — `scripts/hermes/railway_logs.py`: read-only logs via the Railway
  GraphQL API; unblocked the log-triage skill (was a stub).
- **#835 (Q-0130)** — `scripts/hermes/railway_vars.py`: env-var read+write (list/get/set/unset;
  masked list, audit lines, stdin secrets, `--no-deploy`). Owner explicitly granted env-var
  write access (a T3 subset; deploy/restart/scale/rollback stay maintainer-only).
- **#836** — token config aligned to `RAILWAY_TOKEN` (matches Railway's own UI hint) + a
  "which token? (account vs project)" guide; `--whoami` now project-token-aware.
- **#837 (Q-0131)** — manual-step risk-labelling rule in `maintainer-working-profile.md`: the
  owner follows provided steps without vetting → label the risk class (✅/↩️/⚠️) of every
  manual step; never bury a destructive action in routine-looking steps.

## ▶ Handoff — verify Railway live (first thing, next fresh session)
The owner configured these in the **agent env AFTER** this session, so this container can't see
them (confirmed: all four `False` this session). Config:
`RAILWAY_API_TOKEN` (account token, scope=Account) ·
`RAILWAY_PROJECT_ID=285dfbcd-0ba7-42a5-ba87-6d85263a0a37` ·
`RAILWAY_SERVICE_ID=eac6b498-6db7-420e-9d0b-a625941c6504` ·
`RAILWAY_ENVIRONMENT_ID=429efe45-7995-4046-91ce-1886692c33a7`. Network access = **Full**.
**Run:** `python3.10 scripts/hermes/railway_logs.py --whoami` (should print the account), then
`python3.10 scripts/hermes/railway_vars.py list` (bot's vars, masked). Green ⇒ logs + env-var
tooling fully operational. "Not Authorized" ⇒ the account token is fine; recheck the IDs.

## Ledger note (for the due Q-0107 reconciliation routine)
Recently-shipped now carries my 7 PRs. **#824 / #830 / #833** (concurrent routine work) remain
missing from the ledger, and the list is over the soft-20 budget (needs archiving) — both left
to the due reconciliation pass (Q-0124: a manual session does not run it).

## 💡 Session idea (Q-0089)
**Env-var drift check.** A read-only check (on `railway_vars.py`) that diffs production's
variable *names* — never values — against a committed `docs/operations/expected-env-vars.md`
allowlist, flagging a missing-in-prod or unexpected var before it crashes the bot. Secret-safe
(names only), fits the read-only-safe ethos, and turns the new write tooling into a guardrail.
Medium; grooming-lane.

## ⟲ Previous-session review + system improvement (Q-0102)
The session chain has been deep on the P0 hardening spine + the band-820 reconciliation; this
manual session legitimately diverged (owner-directed). **What worked, worth promoting:** the
git-ancestor `Monitor` (`git merge-base --is-ancestor <head> origin/main`) is a *reliable*
merge-confirm backstop where the webhook merge signal is inconsistent — it caught every one of
this session's 7 merges, sometimes before the webhook. Candidate to standardize as the
merge-watch for auto-merge PRs. **Improvement surfaced:** the harness's `send_later` instruction
fires every session but the tool isn't provisioned here (Q-0129 journal note); if it stays
absent, the recurring per-session noise is worth an upstream flag.

## Context delta
In-repo orientation was sufficient (CLAUDE.md / collaboration-model / router / working-profile +
the existing `scripts/hermes/` skills + `production-deployment.md` were exactly what I needed).
The only gap was **external**: the Railway GraphQL API shape (logs + variables queries, the
`Authorization: Bearer` vs `Project-Access-Token` split) is not in the repo — needed web research
(docs.railway.com cookbook + manage-variables). Now encoded in the two scripts +
`production-deployment.md` § "Which Railway token?" / "Env variable read/write", so the next
session does not re-derive it.
