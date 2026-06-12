> **Status:** `audit`

# 2026-06-12 — Hermes Discord dispatch bridge

**PR:** [#757](https://github.com/menno420/superbot/pull/757) — Add Hermes Discord integration: /bugreport and /dispatch slash commands
**Branch:** `claude/stoic-allen-g919wx`

## What was done

- **`HermesCog` (`disbot/cogs/hermes_cog.py`)** — two admin-only slash commands that close the Discord→Hermes→Claude Code loop:
  - `/bugreport <title> <description> [notes]` — formats a `CLASS:fix` work order and POSTs it to the Claude Code Routine `/fire` endpoint; routine self-merges on green CI (Q-0113).
  - `/dispatch <work_order>` — raw work order for any task class; features open a PR but wait for owner approve/deny (Q-0114).
  - Both respond ephemerally, use `safe_defer`, and degrade gracefully with a setup guide when env vars are missing.
- **CI rounds (3):** (1) surface-ledger pin — `bugreport`/`dispatch` added to `EXPECTED_SLASH_SURFACE`; (2) `safe_defer` invariant — replaced raw `interaction.response.defer` calls; (3) doc counts — updated `36→37` loaded-extension counts in both surface-map docs and added `hermes_cog` to the cog list.
- **Grooming move (previous session idea, Q-0089):** Added reconciliation-due advisory to the SessionStart banner (`scripts/claude_session_summary.py`). Now shows `Recon: not due (…)` at boot, and a loud `⚠ RECONCILIATION PASS DUE` warning when the Q-0107 cadence fires — so sessions know *before* doing feature work whether to be a planning pass.

## Decisions recorded

- No new Q-blocks. The user confirmed that Hermes→Discord posting (the other direction) will be configured manually in a separate session.

## Left open / next session

- The user is wiring Hermes to a Discord channel (Hermes posts updates there; channel members can trigger dispatch by talking in it) in a separate conversation. The slash commands in PR #757 are additive and orthogonal to that wiring.
- Four Railway env vars (`CLAUDE_ROUTINE_FIRE_URL` / `CLAUDE_ROUTINE_TOKEN` / `CLAUDE_ROUTINE_BETA` / `CLAUDE_ROUTINE_VERSION`) must be added before `/bugreport` and `/dispatch` are live.

## 💡 Session idea

**Idea:** Natural-language ops-channel listener — the bot watches a designated private ops channel (`HERMES_OPS_CHANNEL_ID` env var) and treats any message from a whitelisted user as a plain-English work order, forwarding it to the Routine without needing the `/dispatch` slash command.
**Why:** The user's vision is "users with access to the channel can just talk to trigger Hermes." Slash commands require Discord UI knowledge; a message listener in a private ops channel is frictionless — type a sentence, the bot assembles the work order and fires it. Same safety model (admin-only channel + env-var whitelist), much lower barrier.
*Small — recorded here only; execute when the user confirms the Hermes channel setup is in place.*

## ⟲ Previous-session review

Reviewing `2026-06-12-reconciliation-cadence-rule.md` (the Q-0107 cadence rule session):

- **What it did well:** shipped a concrete, tested guard (`check_reconciliation_due.py` + 9 tests) and wired it into `/session-close` immediately. The session idea (surface the guard at *boot*, not just close) was exactly the right follow-through — and it was noted clearly enough that this session executed it within the grooming pass.
- **What it could improve / system improvement:** The session idea was captured in the session log but NOT added to `docs/ideas/README.md`, so it lived only in the log text. Small ideas that are "execute next session" candidates should get at least a one-liner in the README so the grooming pass doesn't require reading every log. → The fix: when an idea is explicitly tagged "execute next session," add a TODO bullet to `docs/ideas/README.md` even for small ones. (Not implementing this rule change now — proposing it as a Q-block for Q-DISCUSS consideration.)
