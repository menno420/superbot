# Session: Hermes tooling runs under python3 (VPS has 3.11, not 3.10)

> **Status:** `complete` — PR #869; born-red card flipped as the deliberate final step (Q-0133).

**Branch:** `claude/sharp-ptolemy-5mzbvb` · **Date:** 2026-06-14 · **Type:** fix (tooling portability, Q-0142 follow-up)

## What this session did

Hermes (on the VPS) reported he couldn't rebuild the dispatch skill: the documented commands use
`python3.10`, but the VPS only has `python3` (3.11). Root-caused and fixed.

**Root cause.** Every Hermes-run script is **stdlib-only and version-agnostic** (`build_skills.py`,
`check_current_state_ledger.py`, `check_phase_gate.py`, `routine_fire.py`, `railway_*` — all already
shebang `#!/usr/bin/env python3` except the ledger guard, all run fine under 3.11). But the
Hermes-facing docs/skills hard-coded `python3.10` in their invocation lines. The `python3.10` pin in
`.claude/CLAUDE.md` is **only** for CI-parity tools (`check_quality` / black / mypy / pytest) — which
Hermes never runs — so these stdlib utilities should just use `python3`. My own Q-0142 STEP 1b had
introduced a `python3.10 check_current_state_ledger.py` command Hermes couldn't run; fixed here too.

**Fix.** Changed `python3.10 ` → `python3 ` in the Hermes-facing invocation lines:
- `hermes-skills/dispatch.md` (STEP 1b ledger guard + STEP 2 phase gate) → regenerated `dispatch/SKILL.md`
- `hermes-skills/log-triage.md` (railway_logs) → regenerated `log-triage/SKILL.md`
- `hermes-skills/skill-author.md` (build_skills + check_docs), `hermes-skills/README.md` (build_skills)
- `scripts/hermes/build_skills.py` usage strings + a WHY-`python3` docstring note so nobody reverts it
- `hermes-skills/repo-health.md` Notes — reframed to "use python3; the 3.10 pin is CI-parity-only"

**Untouched (correctly):** `.claude/CLAUDE.md`, CI workflow, and all `check_quality`/formatter/test
references stay `python3.10` — those are the real CI-parity tools. `install-skills.sh` already does
`python3.10 || python3` fallback.

**Owner action:** the install on the VPS now works with `python3 scripts/hermes/build_skills.py`. After
pulling, re-run the install/rebuild; re-paste the regenerated `superbot-dispatch` skill into Hermes.
(Optional alternative for full uniformity: install Python 3.10 on the VPS — but the version-agnostic
fix means that's no longer required.)

Verification: `build_skills.py --check` clean (idempotent under python3); no `python3.10` left in any
`skills/*/SKILL.md`; `check_current_state_ledger.py` + `check_phase_gate.py` run under plain `python3`;
`check_docs --strict` ✓. Docs/tooling only — no runtime bot code.

## 💡 Session idea (Q-0089)

A tiny `build_skills.py --check` is already CI-gated, but there's no guard that catches an *invocation*
regression — i.e. a Hermes-facing doc re-introducing `python3.10` for a stdlib tool. Idea: a one-line
check (extend `check_docs.py` or a `scripts/hermes` test) that fails if any file under
`docs/operations/hermes-skills/` or `scripts/hermes/` contains `python3.10 ` (allowlisting
`install-skills.sh`'s fallback) — so the "Hermes only has python3" constraint is enforced, not just
documented. Captured pending a dedup-grep.

## ⟲ Previous-session review (Q-0102)

The previous run (Q-0142, PR #868) correctly fixed *what Hermes picks* but shipped a command Hermes
literally can't run (`python3.10 check_current_state_ledger.py`) — I added the instruction without
checking it against Hermes's actual environment, the exact "green tests ≠ runs in the target env"
gap. This session closes it. System improvement surfaced: agent-facing tooling docs should be
validated against the *consumer's* environment (Hermes = python3-only VPS), not just the authoring
repo (which has python3.10) — the proposed invocation-guard above makes that structural.
