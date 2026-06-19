# 2026-06-19 — Repo structure: governance + supply-chain + CI baseline

> **Status:** `in-progress`

## Arc (what I'm about to do)

Owner uploaded three external repo-review reports (two Dutch research passes + a Markdown
review reconciling them) and asked for **a comprehensive plan to improve the repo structure**.
Cross-checked every recommendation against live source + recorded owner decisions (the reports
are *input to verify*, never orders — and a prior structure review already settled the
code-layout question: **no filesystem reorg**, Q-0151). The genuine remaining gap is the
**outward-facing governance / supply-chain / operational** layer.

Owner chose, in-session: **LICENSE = MIT**, and scope = **plan + docs + CI config** (greenlighting
the `.github/` executable-config changes in-session — the CLAUDE.md Q-0106 exception; provenance
recorded as **Q-0177**).

This session ships: the comprehensive plan doc + the executed foundation (LICENSE, SECURITY.md,
CONTRIBUTING.md, CITATION.cff, Dependabot, CodeQL, a dashboard-CI job, issue/PR templates) +
a root-fixed dashboard test bug surfaced while wiring the dashboard CI + the routed owner decisions.

_(Enders — context delta, prev-session review, idea, doc audit, run report, telemetry — finalized
in the closing commit when this badge flips to `complete`.)_
