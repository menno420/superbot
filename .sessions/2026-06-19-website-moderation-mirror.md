# 2026-06-19 — Website two-site split: P5 moderation UI + P6 GitHub-issue mirror

> **Status:** `in-progress`

**About to do:** Build units **P5 + P6** of the website two-site-split
(`docs/planning/website-two-site-split-plan-2026-06-19.md` §5). P6 =
`dashboard/github_mirror.py` (least-privilege, idempotent issue-create client built
against a mock). P5 = the owner-gated `/admin/moderation` page + approve/reject
handlers in `dashboard/app.py` + `dashboard/templates/moderation.html`, lists `pending`
via the merged `dashboard/submissions_db.py`, approve → mirror → `attach_issue_url` →
`set_status('approved')`, reject → `set_status('rejected')`. Submissions never shown
publicly; user input rendered escaped. Tests for both. Web tier never imports `disbot/`.

(This card flips to `complete` as the deliberate final step — Q-0133.)
