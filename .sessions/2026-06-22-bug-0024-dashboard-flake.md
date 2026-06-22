# 2026-06-22 — BUG-0024: make the dashboard `generated_at` determinism test hermetic

> **Status:** `in-progress` — bugs-first follow-up (owner: "continue"). Fix the flaky
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

_(filled in as the work lands; flipped to `complete` as the final step)_

## ⟲ Previous-session review

_(end-of-session)_

## 💡 Session idea

_(end-of-session)_
