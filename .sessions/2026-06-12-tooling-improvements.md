# 2026-06-12 — Hermes + tooling improvements

> **Status:** `audit`

**PR:** [#712](https://github.com/menno420/superbot/pull/712) — Hermes skill pack + tooling improvements  
**Branch:** `claude/eager-cerf-ntir3q`

## What was done

- **Fixed and merged PR #710** (voice-mode planning capture): rebased onto current main
  (branch had diverged ~8 commits behind), added link in `docs/ideas/README.md` to fix
  orphan `check_docs` failure. CI green, merged.
- **Fixed and merged PR #711** (Hermes control plane doc): added `living-ledger` status
  badge + navigation row in `docs/repo-navigation-map.md`. CI green, merged.
- **Merged PR #712** (Hermes skill pack): `docs/operations/hermes-skills/` with 6 ready-to-use
  skill prompts — `session-brief`, `repo-health`, `ideas-triage`, `prompt-builder`,
  `open-questions`, `btd6-status`. Each is self-contained and works as a plain Telegram
  message or as a named Hermes skill on the VPS.
- **Added `check_docs` PostToolUse hook** (`scripts/claude_post_edit.py`): markdown file
  edits now trigger `check_docs --strict` and print a loud warning on failure. Catches
  orphan/badge CI failures at edit-time instead of at PR push.
- **Created `/session-close` skill** (`.claude/skills/session-close/SKILL.md`): covers the
  full end-of-session checklist — log, grooming, new idea, quality gate, commit/push, PR
  merge. Compresses the CLAUDE.md session workflow section into a single slash command.
- **Trimmed CLAUDE.md CodeGraph section**: moved the "Use automatically" trigger table and
  trust-tier reference to `docs/codegraph-usage.md` § "When to use automatically". CLAUDE.md
  now keeps only the five critical safety rules. Saves ~35 lines of working context per
  session. Updated `codegraph-usage.md` status badge to reflect it is now the primary
  reference.

## Decisions recorded

- CI triage skill dropped from the Hermes skill pack (owner: CI is auto-handled by Claude,
  not a mobile monitoring need).
- `check_docs` hook is non-blocking (exit 0) — consistent with the Python auto-fix hook;
  the Stop hook remains the hard-fail gate for Python.

## Grooming move

Routed the **craft-and-equip shortcut** and **crafting category filters** (from
`docs/ideas/voice-mode-planning-capture-2026-06-11.md` §4.1/§4.2) to `docs/roadmap.md`
under the Games/Mining "Later" horizon. Both are near-term-quality ideas that need
source verification before planning — adding the roadmap entry gives them a destination.

## Left open / next session

- The session log badge `> **Status:** \`audit\`` is required by `check_docs`; already
  included above.
- The Hermes skill prompts on the VPS still need to be manually configured using the
  files in `docs/operations/hermes-skills/` — that's a maintainer action (SSH to VPS).
- SSH key login for the Hermes VPS is deferred (owner decision).

## 💡 Session idea

**Idea:** Hermes scheduled daily health digest via cron  
**Why:** The `superbot-repo-health` skill exists but requires a manual Telegram prompt.
A single cron entry on the VPS (`0 8 * * *`) running the skill automatically and sending
the result to Telegram would close the monitoring loop — you'd see a red signal in the
morning without having to ask. When everything is green the message is a quiet ✅; only
red days need attention. Zero new infrastructure required — just a cron job and a short
shell script wrapping the existing `hermes gateway` skill call.  
_Small enough to be a maintenance task on the VPS; no repo changes needed._
