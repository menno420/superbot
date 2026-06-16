# Idea — align the lifecycle close-timeout with the platform's kill-grace (defense-in-depth)

> **Status:** `ideas`. Not a plan, not approval. Source + binding contracts win.
> Captured 2026-06-16 (Q-0089 session ender) from the runtime-lock deploy-downtime fix (PR #948).

## The observation

PR #948 fixed the ~85s deploy downtime by releasing the runtime lock **early** (the moment
shutdown begins), so a platform SIGKILL mid-`bot.close()` can't wedge the lock. That's the
primary fix and it stands on its own.

But the investigation surfaced a second, latent mismatch worth closing as **defense-in-depth**:

- `LIFECYCLE_CLOSE_TIMEOUT_SECONDS` is a hardcoded **20s** (`disbot/bot1.py`).
- Railway's observed SIGTERM→SIGKILL grace in the prod log was **~10s** (SIGTERM `08:45:53` →
  container stop `08:46:03`).
- So the close-driver's `os._exit(1)` force-exit fallback (the path meant to fire on a *hung*
  close) **never actually fires in this environment** — the platform kills the process first.

The early lock-release makes this mostly moot for the lock specifically, but the timeout is
still misaligned with reality: any *other* finally-block cleanup (DB close, reporter close)
that the force-exit path was meant to bound is also at the platform's mercy.

## The idea

Make the close timeout **env-configurable** (mirror the existing `RUNTIME_LOCK_BOOT_WAIT_SECONDS`
/ `RUNTIME_LOCK_BOOT_POLL_SECONDS` knobs in `services/runtime.py`), e.g.
`RUNTIME_CLOSE_TIMEOUT_SECONDS`, so an operator can set it **below** their platform's real
kill-grace. Then the in-process force-exit fires *before* the platform's SIGKILL, and the
finally-block cleanup (the parts that aren't already early-released) gets a real chance to run.

Optionally: log the platform grace as **observed** — on SIGTERM, the heartbeat-freeze-to-kill
delta is derivable across boots from the lock row, so a startup line could report "previous
holder's grace ≈ Xs" and flag when the configured close timeout exceeds it.

## What to look into / cautions

- Don't set it *too* low — a legitimately slow-but-valid close (many in-flight interactions)
  shouldn't be cut short. Default should stay generous (the current 20s is fine as a default).
- The real grace is platform-specific and not in the repo (no `railway.toml`); an env knob is
  the right seam, with docs noting "set this under your platform's termination grace."
- Verify against another prod log or two that ~10s is the steady grace (one data point only).

## Disposition

Small, contained, low-risk follow-up to PR #948. Decided-lane (mirrors an existing pattern).
A future session can execute it directly, or fold it into the next runtime-hardening slice.
Relates: `disbot/bot1.py` (`LIFECYCLE_CLOSE_TIMEOUT_SECONDS`), `disbot/services/runtime.py`
(the env-knob pattern), `docs/runtime_contracts.md`.
