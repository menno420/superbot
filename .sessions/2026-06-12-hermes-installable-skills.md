# 2026-06-12 — Hermes: installable skills + operating prompt + log-triage

> **Status:** `audit`

**PR:** [#730](https://github.com/menno420/superbot/pull/730) — make Hermes skills installable + operating prompt + log-triage
**Branch:** `claude/confident-cray-y4plo7`

## Context

Maintainer asked (mobile / exploratory): what's left to finish the Hermes agent he
started setting up yesterday, what can it do that Claude/ChatGPT can't, can it read the
bot's logs to diagnose problems, and can we give it journal-like instructions to orient
faster. Researched the Hermes Agent (Nous Research) docs to ground the answer, then
built the repo-side enablement he approved.

## What was done

- **`scripts/hermes/build_skills.py`** — generates installable `SKILL.md` files (Hermes
  YAML frontmatter) from the `docs/operations/hermes-skills/*.md` docs. Follows the
  `tools/agent_context` source → builder → generated-artifact pattern; pure stdlib so the
  freshness test runs in CI. Docs stay source of truth; artifacts carry a `GENERATED` marker.
- **`scripts/hermes/install-skills.sh`** — copies generated `SKILL.md` into `~/.hermes/skills/`
  on the VPS (`--dry-run`, `--build`). Copies committed artifacts so the VPS needs no toolchain.
- **`repo-health` self-schedules** — `blueprint.schedule: "0 8 * * *"` in its frontmatter →
  Hermes auto-runs the daily health digest once installed. (This *implements* the prior
  session's 💡 "daily health digest cron" idea — see grooming below.)
- **`log-triage` skill** (`docs/operations/hermes-skills/log-triage.md`) — read-only
  production/gateway log diagnosis. The maintainer's "can it read the bot's logs?" ask.
  Triages local `hermes-gateway` logs today; Railway production logs once a **read-only**
  token is set up on the VPS. Diagnoses only — never restarts/redeploys.
- **`docs/operations/hermes-operating-prompt.md`** — the Hermes-side `CLAUDE.md`: standing
  read-only orientation (repo path, read-path order, layer/ownership boundaries, safety
  model). The maintainer's "journal-like instructions to learn faster" ask.
- **`tests/unit/scripts/test_build_skills.py`** — freshness gate; fails CI if committed
  artifacts drift from the docs.
- Wired control-plane doc + skills README + `repo-navigation-map.md` for reachability.

## Verification

- `check_docs --strict` ✓ · `check_quality --check-only` ✓ (black/isort/ruff/check_docs)
- `pytest tests/unit/scripts/test_build_skills.py test_check_docs.py tests/unit/docs/` → 96 passed
- No `disbot/` changes (mypy scope untouched).

## Grooming move

Routed the **owner alerting / dead-man's switch** idea
(`docs/ideas/gap-analysis-2026-06-11.md`) one step forward: this PR's scheduled
`repo-health` digest + `log-triage` skill are the alerting substrate that idea called
for. Annotated the idea with that link (captured → partially routed). Separately, the
prior session's 💡 "Hermes daily health digest cron" reached **shipped** — the
`blueprint.schedule` on `repo-health` is exactly that, no separate cron needed.

## Left open / next session

- **Maintainer VPS actions:** run `bash scripts/hermes/install-skills.sh` then
  `sudo systemctl restart hermes-gateway`; for `log-triage` production logs install the
  Railway CLI with a **read-only** token. SSH-key login still deferred.
- The Hermes→Claude-Code dispatch bridge (this session's new idea) is the next big lever
  for the autonomous loop — see idea file.

## 💡 Session idea

**Idea:** Hermes → Claude Code (web) dispatch bridge — captured as
[`docs/ideas/hermes-claude-dispatch-bridge-2026-06-12.md`](../docs/ideas/hermes-claude-dispatch-bridge-2026-06-12.md).
**Why:** Today Hermes can *prepare* a Claude Code prompt (`prompt-builder`) but the
maintainer still has to open a session and paste it. If Hermes could *trigger* a Claude
Code-on-the-web session from Telegram (via the web trigger/API), the loop closes: idea on
your phone → Hermes orients + dispatches → Claude Code builds, tests, opens a PR, self-
merges → Hermes reports back. That is the "nearly fully autonomous from anywhere" the
maintainer is excited about, with the safety split intact (Hermes decides/dispatches
read-only; Claude Code builds under CI gates). Needs API-surface research → discuss lane.
