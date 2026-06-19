# 2026-06-19 — Bot-site changelog + status pages (P3)

> **Status:** `in-progress`

Building unit **P3** of the website two-site split
([plan](../docs/planning/website-two-site-split-plan-2026-06-19.md) §5) on the merged
foundation (S1+S2+P1, #1109/#1110). Exclusive files only — two templates + their test;
no `botsite/app.py`, no producer, no other template edits.

## About to do

- `botsite/templates/changelog.html` — a timeline grouped by date from
  `site.json.bot_changelog`, kind tags (feature/fix/improvement), honest copy, **no raw
  internal PR numbers** surfaced.
- `botsite/templates/status.html` — a user trust band from `site.json.meta.build`
  (online-as-of-last-deploy · build SHA/date) with a **"generated" freshness badge**
  (no live claim, plan §3).
- `tests/unit/botsite/test_changelog_status.py` — `importorskip`-guarded smoke tests.

Verify: `python3.10 scripts/check_quality.py --full` + `check_architecture --mode
strict`. Ship: ready PR to `main`, auto-merge armed.

<!-- close-out (Q-0089 idea / Q-0102 review / Q-0104 audit / run report) is appended as the final step, then this status flips to complete. -->
