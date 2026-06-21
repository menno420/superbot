# 2026-06-21 — Website count reconciliation + pin-drift guard (rebuilt after parallel-work collision)

> **Status:** `complete`

## Arc

Overnight, PR #1207 hit `conflict-guard` failure: a parallel routine had **already merged overlapping
fixes** to `main` — re-pinned ruff `0.15.18→0.15.14` and fixed the data.js test-clobber as its own
`BUG-0022` (tmp-path arg). My overnight `BUG-0020/0021/0022` numbers all collided with different
already-merged bugs, and my ruff-pin + data.js-test changes were redundant/superseded. Rather than
force a messy conflict resolution of redundant work, I **reset to main and rebuilt the PR to only the
genuinely-novel, non-overlapping value.**

## Shipped (slimmed PR — docs + one guard)

- **BUG-0023 (documented):** the owner's command-count question — bot `354 (283 prefix · 71 slash)`
  vs site `~280` are three different metrics (live-registry-per-surface-incl-subcommands vs unique
  names; source scan = 283 prefix matching the bot exactly + 25 slash → deduped 280). The one real
  gap = slash under-coverage (25 static vs 71 live → dynamically-registered/context-menu commands the
  AST can't see) = scoped INVESTIGATE. Documented in the bug book, `website-explained.md`, and
  migration-plan §9 (display parity = React PR1). *(Renumbered from my overnight BUG-0021, which
  collided with a merged bug.)*
- **`scripts/check_tool_pins.py` + wired into `check_quality.py`:** main fixed *this instance* of the
  ruff pin drift but added **no recurrence guard**. This asserts black/isort/ruff/mypy match between
  `code-quality.yml` and `requirements-dev.txt` (verified it fails on drift), so the next dependabot
  one-file bump is caught pre-PR — the durable stays-fixed guard for main's pin fix.

**Dropped from the overnight version (already on main):** ruff re-pin, the data.js byte-equality→
structural test change (main kept byte-equality + fixed the clobber root cause differently — deferred
to their approach), and the colliding BUG-0020/0022 entries.

Verification: `check_quality --check-only` ✓ (incl. new pin guard) · `pytest tests/unit/botsite/` ✓ ·
`check_docs --strict` ✓ · `check_plan_homing --strict` ✓.

## ⚑ Self-initiated (Q-0172)

Owner-authorized "implement durable/correct fixes." Net contribution after de-duping against parallel
work: the count-reconciliation docs (owner's question) + the pin-drift recurrence guard.

## 💡 Session idea (Q-0089)

**A pre-flight "is my planned change already on main / claimed?" check for autonomous sessions.**
Tonight ~60% of my overnight PR was redundant because a parallel routine fixed the same area while I
worked unattended. `active-work.md` exists for *claims*, but an autonomous session that opens a PR
hours later should re-diff its intended files against `origin/main` HEAD right before pushing (a
`scripts/check_overlap.py` that flags "these files changed on main since you branched"). Would have
caught the ruff-pin + data.js-test overlap before I wrote them. Lane: tooling/workflow.

## ⟲ Previous-session review (Q-0102)

The overnight session (#1207) did the right *investigative* work (found two real traps) but **shipped
unattended into an actively-changing area without re-checking main near push time** — so it collided
with parallel routine work and ~half had to be discarded. **What this run did better:** instead of
force-resolving conflicts to preserve my commit, I deferred to the merged approach and kept only
net-new value. **System improvement:** the idea above (pre-push overlap check) is the concrete guard;
the softer lesson is that high-velocity unattended work should prefer *small, orthogonal* PRs over
broad ones, to minimize collision surface with the routines.

## 📤 Run report

- **Did:** rebuilt #1207 after a parallel-work collision; kept the count-reconciliation docs + a
  pin-drift recurrence guard · **Outcome:** shipped (slimmed)
- **Run type:** `autonomous · self-initiated (conflict recovery + de-dup)`
- **⚑ Owner decisions needed:** none new (React migration still §3-gated; BUG-0023 slash-coverage scoped)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** count docs + `check_tool_pins.py` guard (owner-granted)
- **↪ Next:** BUG-0023 slash-coverage INVESTIGATE (focused session) · React migration on owner "go"

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#1207 rebuilt — docs + 1 guard) |
| Runtime (`disbot/`) code changed | 0 |
| Work discarded as redundant (parallel routine) | ~half the overnight PR (ruff pin, data.js test, 2 bug entries) |
| New tooling | 1 (`check_tool_pins.py`, wired into `check_quality.py`) |
| Bugs documented | 1 (BUG-0023 count metrics + slash-coverage INVESTIGATE) |
| New ideas contributed | 1 (pre-push overlap check for autonomous sessions) |
