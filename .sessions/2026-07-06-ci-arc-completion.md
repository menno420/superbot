# 2026-07-06 — CI-arc completion: 2nd AST guard + tail cleanup

> **Status:** `in-progress` — born-red card (Q-0133). Follow-up to the merged #1747 (check_audit_seam).
> Owner directive: *"finish everything you can do without my help; choose decisions yourself."* So this
> session completes the **safe, self-contained** remainder of the CI-followups arc
> (`docs/planning/ci-followups-handoff-2026-07-05.md`) and makes the design calls itself — while
> respecting the safety brakes (no branch-protection required-context swap, no `.claude/settings.json`
> or hook edits; those either can't be done from code or affect every session and stay owner-gated).
> Flips to `complete` as the deliberate final step once `check_quality --full` is green.

## Scope this session

- **`check_deferred_recovery.py`** (handoff #5, second AST guard) — key on the spawn-target
  (`tasks.spawn`/`create_task`/`ensure_future`), resolve the callee, flag a spawn-target whose body
  does `asyncio.sleep` then a Discord state mutation but lacks a persisted-deadline write + boot
  reconcile. Advisory, warn-first, allowlist. The restart-recovery-gap class the Stage-2 walk found
  twice by hand.
- **Tail cleanup:** delete dormant `check_doc_freshness` (G7); document the #794-class
  content-completeness race as accept-advisory (G8); verify `check_session_slug_unique` CI-context.
- **Assess** the `ci.yml`/`web-ci.yml` restructure (handoff #4) — build-alongside vs document.

_(Enders filled at close, then this badge flips to `complete`.)_
