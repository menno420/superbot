# 2026-06-17 — Open the idea→plan gate (Q-0172) + skills batch-1 slim

> **Status:** `in-progress`
> Manual, owner-directed live. **Born-red per Q-0133** — edits `.claude/CLAUDE.md` (a governance
> change the owner directed in-session, Q-0106 → applied directly). Flip to `complete` as the final
> step once CI is green.

**Branch:** `claude/skills-batch1-reconciliation` · **PR:** #1029 (repurposed from batch-1 slim → governance)

## Goal

The owner observed the autonomous loop "running out of plans" and traced it to ideas never becoming
plans — canonical case **fishing** (the ratified ecosystem-#2 verdict, V-14 teardown), never planned.
His fix, directed in-session: **remove the idea gate** — ideas may become plans/builds anytime without
approval, flagged in the session log so he / Hermes / another chat can see, filter, review. Implemented
as **Q-0172**.

## What was done

**Q-0172 — open the idea→plan gate (owner-directed, Q-0106 applied directly):**
- `.claude/CLAUDE.md` — rewrote the "A new idea is not a new priority" bullet: any agent may promote
  idea → plan → implementation anytime, no approval; flag it `⚑ Self-initiated`. **Kept** the focus
  discipline (don't derail the *current* task), the classify-into-`docs/ideas/`-first habit, and the
  safety brakes (irreversible/production still ask-first).
- `scripts/check_phase_gate.py` — demoted to **advisory-only** (banner + docstring; exit codes
  unchanged so `test_check_phase_gate.py` stays green).
- Dispatch routine prompt + skills (`hermes-dispatch-bridge.md`, `hermes-skills/dispatch.md`,
  `scripts/hermes/skills/dispatch/SKILL.md`) — self-invented features now build+ship (flagged), not
  blocked; empty-fire may promote an idea→plan when the backlog is thin. `autonomous-routines.md`,
  `hermes-control-plane.md`, `hermes-terminal-cheatsheet.md`, `hermes-skills/README.md` — gate
  references updated to "advisory."
- `.sessions/README.md` — new `⚑ Self-initiated:` run-report line + explanation.
- `scripts/export_dashboard_data.py` + `dashboard/templates/updates.html` — parse + amber badge the
  self-initiated flag so the owner can filter/review unprompted work on the website.
- `docs/owner/maintainer-question-router.md` — **Q-0172** recorded.

**Doc updates (owner: "yes please update the documents"):**
- `docs/ideas/codex-automated-pr-review-2026-06-17.md` + router **Q-0171 → LIVE** (Codex enabled
  2026-06-17, auto-reacting 👍 on PRs; the bare reaction isn't readable via `get_reviews`/`get_comments`,
  but real reviews are + the PR-activity subscription delivers them into a watching session).
- `docs/current-state.md` — **ledger drift fixed** (#1025–#1028 added to Recently shipped) + ▶ Next
  action de-staled to announce the open gate + **fishing** as the canonical first promotion.
- Cron 2h→3h reflected in the dispatch prompt + routines registry (owner tuned it for weekly limits).

**Skills batch-1 (rides along, owner-approved direction):** the Q-0107 reconciliation-bullet slim →
thin pointer (PR #1029's original scope; kept — a clean improvement on a different CLAUDE.md section).

## Kept vs moved (governance audit, per the batch convention)

- **Kept in CLAUDE.md:** the focus discipline, classify-first, safety brakes, all Q-numbers; the
  reconciliation cadence + manual-session carve-out (batch-1).
- **Changed in CLAUDE.md:** the idea bullet flips from "not promoted without owner say-so" → "promote
  freely, flag it." Net governance shift: **pre-approval → post-hoc review.**

## Decisions recorded

- **Q-0172** — open the idea→plan gate (owner-directed in-session, applied directly per Q-0106).
- **Q-0171** — Codex PR review is now LIVE.

## Left open / next session

- **Hermes plain-language format rollout** — PR 2 this session (owner greenlit it).
- **Build the fishing plan** — the canonical first self-initiated promotion under Q-0172 (any agent
  can now; flag it ⚑ Self-initiated).
- Skills conversion batches 2–4 (the procedures→skills plan).

## 💡 Session idea

**Idea:** `check_self_initiated_flag.py` — a warn-only guard that flags when a PR adds a **new**
`docs/planning/*` plan or a new cog **without** a non-`none` `⚑ Self-initiated:` run-report line and
without a dispatched/owner trigger. **Why:** Q-0172 trades pre-approval for accountability, and that
trade only holds if the flag is reliably *present*; a cheap stdlib guard keeps self-initiated work from
merging silently unflagged (it would defeat the owner's whole "filter and review" ask). Disposable
(Q-0105) — delete if it proves noisy.

## ⟲ Previous-session review

The previous session (#1028 / the batch-1 work) was right to **hold the CLAUDE.md edit born-red for
owner review** rather than auto-merge — that pause is exactly what let the owner expand a 10-line slim
into the much larger Q-0172 governance change. **System improvement it surfaces:** the idea gate had
been quietly *causing* the plan shortage for days while every session dutifully followed it. Sessions
should run an occasional **"rule health check"** — is a standing CLAUDE.md rule still serving the goal,
or has it become friction? — instead of only ever obeying rules. (Captured here as a behavior to fold
into the Q-0102 review prompt, not a new doc.)

## 📤 Run report

- **Did:** opened the idea→plan gate (Q-0172) + accountability flag + dashboard badge; Codex→live; ledger drift fixed · **Outcome:** shipped
- **Shipped:** #1029 — governance: open the idea→plan gate (Q-0172) + batch-1 slim + doc updates
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none` (you directed Q-0172; flag me if the scope overshot — it's reversible)
- **⚑ Owner manual steps:** **re-paste the dispatch routine prompt** into the console — it changed (idea-gate removal + ~2–3h cron wording). The reconciliation prompt is unchanged this session.
- **⚑ Self-initiated:** `none` (everything this run was owner-directed or owner-requested) (Q-0172)
- **↪ Next:** Hermes format rollout (PR 2, this session) → then any agent can promote **fishing** → a plan + build it

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 so far (this PR + the Hermes PR pending) |
| CI-red rounds | TBD (filled at flip-to-complete) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`check_self_initiated_flag.py`) |
| Ideas groomed | 1 (fishing → teed up as the canonical Q-0172 promotion) |
