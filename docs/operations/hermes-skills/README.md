# SuperBot — Hermes Skill Pack

> **Status:** `living-ledger` — operational reference for the SuperBot-specific Hermes
> skills. Each skill is a ready-to-configure prompt for the Hermes agent running on the
> control-plane VPS. Setup context: `docs/operations/hermes-control-plane.md`.

This pack contains seven skills covering the windows Hermes fills that Claude Code
cannot: **pre-session orientation**, **between-session monitoring**, and
**production diagnosis from your phone**.

For the standing read-only operating instructions every Hermes session should start
with, see [`hermes-operating-prompt.md`](../hermes-operating-prompt.md) — the Hermes-side
equivalent of `.claude/CLAUDE.md`.

---

## Skills

| Skill | Window | Purpose |
|---|---|---|
| [`session-brief`](./session-brief.md) | Pre-session | Compressed orientation brief to paste into Claude Code |
| [`repo-health`](./repo-health.md) | Between sessions | Traffic-light snapshot — is anything broken? (self-schedules a daily digest) |
| [`ideas-triage`](./ideas-triage.md) | Downtime | Ideas backlog review with a suggested next move |
| [`prompt-builder`](./prompt-builder.md) | Pre-session | Turn a spoken idea into a structured Claude Code prompt |
| [`open-questions`](./open-questions.md) | Between sessions | Surface unanswered Q- blocks from the router |
| [`btd6-status`](./btd6-status.md) | After live testing | BTD6 data pipeline coverage and open items |
| [`log-triage`](./log-triage.md) | After a deploy / when the bot misbehaves | Read production logs and diagnose what's wrong (gated on a read-only log source) |

---

## How it's built and installed

These `.md` files are the **human-readable source of truth** for each prompt. Hermes
loads skills as `SKILL.md` files with YAML frontmatter, so a small builder generates
those from these docs (the same source → builder → generated-artifact pattern as
`tools/agent_context/`):

```bash
# Regenerate the installable SKILL.md artifacts after editing any skill doc:
python3.10 scripts/hermes/build_skills.py
```

This writes `scripts/hermes/skills/<name>/SKILL.md` (frontmatter + prompt body, marked
`GENERATED — DO NOT EDIT`). **Edit the doc here, never the generated `SKILL.md`.** A test
(`tests/unit/scripts/test_build_skills.py`) fails CI if the committed artifacts drift
from the docs.

To install on the VPS (run as the `hermes` user, from the repo root):

```bash
bash scripts/hermes/install-skills.sh            # copies SKILL.md files into ~/.hermes/skills/
bash scripts/hermes/install-skills.sh --dry-run  # preview
sudo systemctl restart hermes-gateway            # pick up the new skills
```

Hermes loads any `SKILL.md` under `~/.hermes/skills/` on next run — no registration step.
Alternatively, each prompt is self-contained and works as a plain Telegram message too.

`repo-health` ships a `blueprint.schedule` (`0 8 * * *`) in its frontmatter, so once
installed Hermes self-schedules the daily health digest to your home channel — no extra
cron wiring needed.

---

## Shared operating rule (every skill)

All skills default to **read-only**. None of them modify repo files, commit, push,
create PRs, or access Railway/Neon/production secrets. If a skill produces an
implementation prompt, the prompt is an artifact for Claude Code — Hermes does not
execute it.
