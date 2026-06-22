# 2026-06-22 — BUG-0024: make the dashboard `generated_at` determinism test hermetic

> **Status:** `complete` — bugs-first follow-up (owner: "continue"). Fix the flaky
> `test_generated_at_is_deterministic_not_wall_clock` (BUG-0024): it depends on a real `git`
> subprocess (`timeout=5`) that saturated `pytest -n auto` workers can blow, triggering the
> production wall-clock fallback so two `build_data()` calls differ. Make the test hermetic by
> pinning `_git_meta` (the BUG-0021 real-clock-injection pattern). Owner-directed continuation →
> merge on green; no `needs-hermes-review`.

> **Run type:** `manual · owner-directed`

## Root cause

`export_dashboard_data._git_meta` runs `git` with `timeout=5, check=True`; under `-n auto` load a
call can time out → returns `{}` → `generated_at` falls back to `datetime.now()` (wall-clock). The
test calls `build_data()` twice and asserts the two `generated_at` values are equal — true only when
git succeeds both times. The **production** logic is correct (commit time is deterministic; the
fallback is an intentional git-absent degrade); only the **test** is non-hermetic.

## What shipped

- **`tests/unit/scripts/test_export_dashboard_data.py`** — `test_generated_at_is_deterministic_…`
  now pins `_git_meta` (monkeypatch) so it exercises the determinism logic without a real `git`
  subprocess that can time out under `-n auto`. Verified **35/35 under `-n auto` ×3** (the exact
  flake condition) + green in isolation.
- New **`test_generated_at_falls_back_to_wall_clock_when_git_unavailable`** — covers the intentional
  git-absent fallback branch, so both branches stay tested.
- **`docs/health/bug-book.md`** — BUG-0024 → `FIXED (root)` with confirmed root cause + the
  stays-fixed guard named.
- **Pruned my own stale claim** `claude__ci-rerun-watchdog.md` (PR #1288 merged via squash —
  drift-on-sight Q-0166; exactly what `check_stale_claims` exists to catch).
- **No production change** — the wall-clock fallback was always correct; only the test was
  non-hermetic.

> **⚑ Self-initiated:** none — owner-directed continuation ("continue from where you left off");
> bugs-first per CLAUDE.md. Merge on green, no `needs-hermes-review`.

## ⟲ Previous-session review

The previous session (the `ci-rerun-watchdog` build, this same chat) did well to mirror the proven
`pr-auto-update.yml` patterns (ROUTINE_PAT, claude/* scoping, Q-0105 header) rather than invent a
mechanism, and to keep the re-kick loop-safe via the presence-check. **What it missed:** it flipped
the card to `complete` but **did not delete its own claim file** — so `claude__ci-rerun-watchdog.md`
landed stale on `main` (I pruned it here). **System improvement this surfaces:** the per-claim
self-delete at close is currently unenforced — only the reconciliation GC (`check_stale_claims`,
every 30 PRs) catches a forgotten one. A cheap closer is a Stop-hook / SessionStart nudge: "your
branch's PR is merged but `docs/owner/claims/<branch>.md` still exists — delete it." That moves the
catch from "every 30 PRs" to "next session," tightening the loop the watchdog work itself relies on.

## 💡 Session idea

**Idea — a `check_consistency` rule for the recurring flake class.** BUG-0021 and BUG-0024 are the
same shape: a test whose assertion path depends on **real wall-clock (`datetime.now()`) or a real
`subprocess`/`git` call** that races under `pytest -n auto`. A small AST rule could flag a test
function that calls `datetime.now()`/`time.time()` or `subprocess.run([...])` *and* has an `assert`
on the result, nudging "inject the clock / pin the subprocess (see BUG-0021/0024)". Warn-only,
allowlistable, Q-0105 disposable — it turns a twice-seen flake class into a guard so the next one is
caught at write time, not in a flaky CI run. (Dedup-checked `docs/ideas/` — not present.)
