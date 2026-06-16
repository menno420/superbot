# Developer dashboard (personal website) for SuperBot

> **Status:** `ideas` — owner-requested **and approved** 2026-06-16 (router Q-0154).
> Phase 1 (read-only MVP) shipped in **PR #967**; the fuller vision (Phases 2–4) stays
> active. **Authoritative plan:**
> [`docs/planning/developer-dashboard-plan.md`](../planning/developer-dashboard-plan.md).
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

## Status / next

* **Phase 1 ✅ shipped (PR #967)** — read-only MVP: function catalogue, ideas, bugs,
  updates feed, public showcase. Decoupled FastAPI app under `dashboard/`, fed by
  `scripts/export_dashboard_data.py`.
* **Phases 2–4 (active):** auth + checklist + public bug-report form (→ dashboard +
  GitHub); env/secrets usage-map then Railway-backed management; multi-AI control board.

→ relates `dashboard/` · `scripts/export_dashboard_data.py` ·
`docs/planning/developer-dashboard-plan.md`.
