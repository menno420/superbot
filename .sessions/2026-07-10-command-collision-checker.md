# 2026-07-10 — command-collision checker (overnight shift, session A)

> **Status:** `in-progress`
> **Branch:** `claude/command-collision-checker` · **PR:** (opens with this commit)

**Intent:** implement `scripts/check_command_collisions.py` + tests — the static
duplicate-command guard from `docs/ideas/command-collision-checker-2026-06-29.md`
(gate `ready`; prevents the #1541/#1544 `give` collision prod-outage class). CI
wiring into `code-quality.yml` is deliberately deferred (workflow edits are out of
overnight scope) and noted as a follow-up in the idea file. Also dispositioning
open PR #1917 (codex docstring-only PR) per the shift plan.
