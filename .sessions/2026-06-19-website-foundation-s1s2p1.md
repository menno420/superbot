# 2026-06-19 — Website two-site split: serial foundation (S1 + S2 + P1)

> **Status:** `in-progress`

Building the **serial foundation** of the website two-site-split per
`docs/planning/website-two-site-split-plan-2026-06-19.md` §5: the three disjoint
foundation units that everything downstream depends on.

- **S1** — extend `scripts/export_dashboard_data.py` to also emit
  `botsite/data/site.json` (a redaction-by-construction public subset), fold in the
  `bot_changelog` parse, seed `docs/bot-changelog.md`, register `site.json` in the
  freshness/whitelist guards.
- **S2** — the `submissions` table DDL + two independent access helpers
  (`botsite/submissions_db.py` INSERT-only; `dashboard/submissions_db.py` read/moderate).
- **P1** — the bot-site FastAPI app (`botsite/`) with every route wired up front + an
  empty `/submit` stub router.

Scope fence: foundation only (no P2–P8, no control-manager, no `disbot/` edits, no deploy).

<!-- This card is born-red (in-progress) per Q-0133: the check_session_gate step in
code-quality holds the auto-merge until the Status flips to `complete`. The close-out
docs (Context delta, idea, previous-session review, run report) land before that flip. -->
