# Developer dashboard (personal website) for SuperBot

> **Status:** `ideas` — owner-requested **and approved** 2026-06-16 (router Q-0155), now **LIVE**
> at https://superbot-dashboard.up.railway.app. Shipped: #967 (MVP) · #969 (env map) · #972
> (commands explorer) · #973 (count reconcile); Phases 2 + 3b + 4 remain. **Authoritative plan +
> handoff:** [`docs/planning/developer-dashboard-plan.md`](../planning/developer-dashboard-plan.md).
> This file is the backlog capture; the plan governs.

## The request

Owner (2026-06-16): *"build me a personal website that's linked to my project"* — a
developer dashboard usable as a checklist, an update tracker, a bot-function catalogue,
an ideas/bug board, a **public** bug-reporting surface, a way to link multiple AIs
together, and **a place to safely store env values and track where each is used.**

Four shaping decisions (answered in-session): AI linking → **control board over the
current flow**; secrets → **usage map + manage via Railway** (Railway stays source of
truth); bug reports → **dashboard + GitHub-issue mirror**; start → **design doc + a
read-only MVP now**.

## Why it matters

The project already maintains rich structured data — the subsystem registry, the idea
backlog, the bug book, session logs, GitHub PRs, Railway env vars. A dashboard that
**surfaces** that (rather than duplicating it) is low-risk and high-value, and it turns
the agent-network workflow into something the owner can see and steer from one place.
It also gives the project a public face (showcase + public bug intake).

## Status / next — LIVE

**Live at https://superbot-dashboard.up.railway.app** (a second Railway service; auto-redeploys on
merge to `main`).

* **Shipped:** Phase 1 read-only MVP (#967) · env-usage map `/env` (#969) · `/commands` cog & command
  explorer (#972) · command-count reconcile + bot status-embed fix (#973).
* **Next (owner-approved):** Phase 2 (auth + checklist + public bug form → dashboard **and** GitHub
  issue) · Phase 3b (Railway-backed secret management) · Phase 4 (multi-AI control board).
* **The owner is bringing more ideas next session** — see the plan's "Ideas backlog" and
  "⭐ Next session — start here".

The **authoritative record + handoff + live-state + Railway-API how-to** is the plan:
[`docs/planning/developer-dashboard-plan.md`](../planning/developer-dashboard-plan.md).

→ relates `dashboard/` · `scripts/{export_dashboard_data,scan_commands,scan_env_usage}.py`.
