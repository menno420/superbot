# Idea: drive the autonomous cron from an external scheduler (not GitHub `schedule:`)

> **Status:** `ideas` — capture only, **not** a plan and **not** approval for
> implementation. Source code and the binding contracts win over this file.

**Captured:** 2026-06-14 · **Source:** the workflow-health review session (Q-0134/0135/0136) ·
**Lane:** small / decided — implementable when on-time firing matters

## The problem it solves

The autonomous loop's overnight cadence (`executor-nightly.yml`, `backup-db.yml`) relies on
GitHub Actions `schedule:` crons. GitHub's scheduler is **best-effort on low-activity repos** —
observed this session: the executor cron (`17 1,3 * * *` = 01:17/03:17 UTC) fired on time on
2026-06-13 (01:20) but **~4¾ h late** on 2026-06-14 (06:04); the backup cron (02:00 UTC) opened
its failure issues at 06:15 and 06:39 UTC both days (~4 h late). The `:17`-minute offset reduces
top-of-hour congestion but does **not** eliminate the multi-hour variance, and GitHub
occasionally **drops** a scheduled run entirely. So "runs overnight" is true; "runs at 03:17" is
not. If the owner ever wants the loop to fire at a predictable time (e.g. so the docs are fresh
before he wakes), GitHub `schedule:` can't deliver it.

## The idea

Drive the cadence from an **external scheduler that calls `workflow_dispatch`** (which fires
immediately and reliably) instead of GitHub's internal `schedule:`:

- A tiny cron on the **Hermes VPS** (already live, already has `gh`/a token) runs
  `gh workflow run executor-nightly.yml` at the wanted local time — Hermes is the natural home
  for the control-plane's "heartbeat".
- Or a Cloudflare Worker / any uptime-cron service hitting the Actions REST
  `POST /actions/workflows/{id}/dispatches`.
- Keep the GitHub `schedule:` as a *backstop* (so the loop still runs if the external scheduler
  is down), but treat `workflow_dispatch` as the primary, on-time path.

## Why it's worth having

It converts "sometime in a ~5 h window, occasionally skipped" into "at the time I chose, every
day". It also makes the firing **observable** (the external scheduler logs success/failure),
which pairs with the new `check_loop_health.py` control-plane probe (Q-0135). Low effort — one
cron line on a box that already exists.

## Size / route

Small. One scheduled command on the VPS + a doc note. Groom into a control-plane session when
on-time firing becomes a felt need (today the lag is documented and accepted). Until then this
stays captured, not built — the loop *works*, it's just not punctual.
