# 2026-06-19 — Website two-site split, unit P4 (public `/submit` intake)

> **Status:** `in-progress`

## What I'm about to do
Build unit **P4** of the website two-site split (plan
`docs/planning/website-two-site-split-plan-2026-06-19.md` §5) — the public
bug/suggestion `/submit` form + intake on the new bot site. Foundation (S1+S2+P1) is
merged on `main`; this fills P1's empty `botsite/submit.py` stub end-to-end.

Exclusive files (scope-fenced — only these):
- `botsite/submit.py` — fill the stub: `/submit` `APIRouter` (GET form, POST
  validate→honeypot→rate-limit→INSERT `pending`→thank-you redirect).
- `botsite/ratelimit.py` — copy the dashboard's proven stdlib sliding-window limiter
  (no shared import, plan §2.2).
- `botsite/templates/submit.html` — the form (category·title·description·surface·
  optional contact·hidden honeypot) + friendly "reviewed, not all ship" copy + an
  accurate privacy note (optional contact + salted IP hash, NOT "no personal data").
- `tests/unit/botsite/test_submit.py` — honeypot drop · validation · insert path
  mocked (no live DB).

Do NOT edit `botsite/app.py`, `botsite/submissions_db.py` (use it), or any other unit.
