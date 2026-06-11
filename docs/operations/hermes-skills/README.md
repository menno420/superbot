# SuperBot — Hermes Skill Pack

> **Status:** `living-ledger` — operational reference for the SuperBot-specific Hermes
> skills. Each skill is a ready-to-configure prompt for the Hermes agent running on the
> control-plane VPS. Setup context: `docs/operations/hermes-control-plane.md`.

This pack contains six skills covering the two windows Hermes fills that Claude Code
cannot: **pre-session orientation** and **between-session monitoring**.

---

## Skills

| Skill | Window | Purpose |
|---|---|---|
| [`session-brief`](./session-brief.md) | Pre-session | Compressed orientation brief to paste into Claude Code |
| [`repo-health`](./repo-health.md) | Between sessions | Traffic-light snapshot — is anything broken? |
| [`ideas-triage`](./ideas-triage.md) | Downtime | Ideas backlog review with a suggested next move |
| [`prompt-builder`](./prompt-builder.md) | Pre-session | Turn a spoken idea into a structured Claude Code prompt |
| [`open-questions`](./open-questions.md) | Between sessions | Surface unanswered Q- blocks from the router |
| [`btd6-status`](./btd6-status.md) | After live testing | BTD6 data pipeline coverage and open items |

---

## How to install on the VPS

Each skill file contains a ready-to-use prompt block. To add a skill to Hermes:

1. SSH into the VPS as `hermes`.
2. Create a skill file in `~/.hermes/skills/` (or the path configured in `~/.hermes/config.yaml`).
3. Paste the prompt block from the skill file into the Hermes skill config.
4. Alternatively, send the full prompt text directly in Telegram — each skill prompt
   is self-contained and works as a plain Telegram message too.

The repo-side skill files are the source of truth. If you update a skill prompt here,
copy the new version to the VPS manually.

---

## Shared operating rule (every skill)

All skills default to **read-only**. None of them modify repo files, commit, push,
create PRs, or access Railway/Neon/production secrets. If a skill produces an
implementation prompt, the prompt is an artifact for Claude Code — Hermes does not
execute it.
