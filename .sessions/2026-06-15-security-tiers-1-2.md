# Session — security service tiers 1+2 (raid detection + account-age filter)

> **Status:** `complete`

**Dispatch:** continued from the live ▶ Next action = **security service tiers 1+2**
(band-#900 decade-queue slot 9, plan-first, Q-0111). Clean slate at start. PR **#929**.

**Scope (substantial new subsystem → Q-0117 `needs-hermes-review`, NOT self-merged;
auto-merge disabled).**

## What shipped
A new hub-less `security` subsystem (the two APPROVED tiers only; tiers 3+4
alt-detection / VPN DECLINED, kept absent — no external calls, no PII):
- **Tier 1 — raid detection:** pure `RaidTracker` (per-guild sliding join window)
  → deduped staff alert (once per lockdown) + optional auto-slowmode on a
  configured channel (bounded window, auto-restored).
- **Tier 2 — account-age filter:** `alert` / `kick` on accounts younger than N
  days; kick routes through `moderation_service.kick` (no parallel action/audit).
- Off by default · fail-open · guardrail-clamped thresholds.
- Files: `services/security_service.py` · `services/security_config.py` ·
  `utils/settings_keys/security.py` (+ `__init__` wiring) · `cogs/security/schemas.py`
  (11 SettingSpecs) · `cogs/security_cog.py` · `events_catalogue` (2 advisory events) ·
  `config.INITIAL_EXTENSIONS` · the 6 new-subsystem cascade touch-points
  (registry · help-surface-map · settings-customization map · nav map) · ownership.md ·
  family-plan §4 row · the pointer-lane ledger (2 channel pointers) + the help
  preamble/top-level-set pins.
- Tests: `tests/unit/services/test_security_config.py` (clamping/predicates) +
  `test_security_service.py` (RaidTracker window · account-age · fail-open
  orchestration · raid dedupe · alert-vs-kick) + `tests/unit/cogs/test_security_schemas.py`
  (defaults alignment · validators) — 37 new tests.

**Verification:** `python3.10 scripts/check_quality.py --full` green (9920 passed)
· `check_architecture --mode strict` 0 errors · `mock_security_alerts` is the UX target.

## Handoff (next routine reads current-state ▶)
- **#929 awaits a human merge** (`needs-hermes-review`, auto-merge disabled). It is
  the band-#900 queue's last buildable-now slot.
- **The band-#900 queue is essentially drained.** Remaining slots are all blocked:
  P1-1 absence-guard Layer B + live-quality battery (creds/review), BUG-0009 slice 3
  newest-towers (data-gated), owner-steered product/loop threads. The **#930
  reconciliation pass** should plan the next band rather than an autonomous run
  forcing a blocked slot.
- Quarantine (a third age-filter action, role isolation) is a documented phase-2
  extension — the `age_action` enum + `_handle_account_age` are shaped to take it
  (add a `quarantine` value + a quarantine-role setting + a `role_automation.apply`
  grant, mirroring welcome's entry role).

## 💡 Session idea (Q-0089)
**Make the PreToolUse hooks cwd-robust (resolve `$CLAUDE_PROJECT_DIR`, not relative
`scripts/`).** This session hit a hard deadlock: a single `cd disbot` (to run an
import smoke-test) left the Bash tool's cwd in `disbot/`, and the repo's two
PreToolUse hooks (`scripts/claude_pre_edit.py`, `scripts/check_branch_freshness.py`)
are invoked with a **repo-root-relative** path — so from `disbot/` they fail
FileNotFound and **block every Bash and Write/Edit for the rest of the turn**. The
fix is one-line per hook: `python3.10 "$CLAUDE_PROJECT_DIR/scripts/<x>.py"` (absolute),
so an agent's working-directory choice can never brick its own tools. **This is
executable config — per CLAUDE.md Q-0106 I do NOT self-edit hooks; recorded here +
as a router DISCUSS Q-block proposal for the owner.** Genuinely believe in it: it's
a small, high-leverage robustness fix that would have saved this session a ~30-minute
recovery dance (worktree-agent commit to preserve uncommitted work).

## ⟲ Previous-session review (Q-0102)
The previous run (#926, BUG-0009 slices 2+2b) did the right structural thing:
it didn't just fix the dispatched Geraldo slice, it introduced the
`deterministic_btd6_list_reply` dispatcher as a clean extension point and folded in
the owner's third named mislabel (mode groupings) in the same PR — high-leverage,
finished work. Nothing to fault in it. The concrete **system** improvement this
session surfaces is the hook-cwd fragility above (Q-0089) — orthogonal to #926, but
it's the genuine "assume the system is still in development" finding: the workflow
should be robust to an agent's own `cd`, and currently isn't.

## Doc audit (Q-0104)
- `check_quality --full` green; `check_architecture --mode strict` 0; `check_docs
  --strict` + `check_current_state_ledger --strict` run at close (below).
- New owner-decision provenance is Q-0111 (already recorded in the router); no new
  Q-block needed for the build (the cwd-hook idea is a *proposed* DISCUSS Q-block).
- All new code reachable: ownership.md (service + events), family plan §4, the
  4 cascade docs, current-state ledger entry.
- **active-work.md claim:** not added at session start (a process miss — the cwd
  recovery consumed the early-session attention); noting it here for honesty.
