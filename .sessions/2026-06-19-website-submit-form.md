# 2026-06-19 — Website two-site split, unit P4 (public `/submit` intake)

> **Status:** `complete` — PR #1117 (auto-merge armed, SQUASH).

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

## What shipped
- **`botsite/submit.py`** — filled the P1 stub. `GET /submit` renders the form (and the
  PRG thank-you state + a dormant "unavailable" state); `POST /submit` runs
  **honeypot → rate-limit → validate/sanitise → INSERT pending → 303 redirect**. The
  POST delegates validation + the salted-IP-hash to S2's INSERT-only
  `submissions_db.insert_pending` (single write path, never the raw IP). Form body is
  parsed with stdlib `urllib.parse` (no `python-multipart` dep), mirroring the
  dashboard's `_form`. Friendly error/dormant states never leak internal text.
- **`botsite/ratelimit.py`** — verbatim copy of `dashboard/ratelimit.py`'s stdlib
  sliding-window limiter (no shared import, plan §2.2). Two per-IP windows wired in
  `submit.py` (5/min, 24/hr).
- **`botsite/templates/submit.html`** — category(bug/suggestion) · title · description ·
  surface(bot/dashboard/CI/other) · optional contact · a visually-hidden honeypot;
  "every submission is read by a human… not all suggestions ship" copy; an **accurate**
  privacy note (optional contact + a salted one-way IP hash for abuse prevention — does
  **not** claim "no personal data"). Re-populates fields after a rejected post.
- **`tests/unit/botsite/test_submit.py`** — 15 tests: honeypot silent-drop, validation
  (missing title/body, bad kind, value re-population), happy-path INSERT-args + PRG,
  optional→NULL, rate-limit trip, dormant friendliness, reachability, no-disbot. The
  INSERT spy stays faithful (runs the store's `build_insert`) so it never opens a DB yet
  still exercises the route's real exception handling.

### One out-of-fence edit (necessary, flagged)
- **`tests/unit/botsite/test_app.py`** — P1's `test_submit_router_is_mounted_but_stub`
  asserted the stub was empty (`submit.router.routes == []`). P4 fills the stub **by
  design**, so that assertion is now false and would redden CI. Updated it to
  `test_submit_router_is_mounted` (asserts the GET+POST routes exist) — the minimal
  change to keep P1's "app.py mounts the router as the single owner" intent true
  post-P4. The route *behaviour* is covered by the new `test_submit.py`. This is the
  only file touched outside the P4 set; `botsite/app.py` and `submissions_db.py` were
  not modified (used as-is).

## Verification
- `python3.10 scripts/check_quality.py --full` → pytest **10910 passed, 37 skipped**;
  black/isort/ruff green over CI's exact scope (a black↔ruff trailing-comma churn on the
  two limiter assignments was resolved to black's stable exploded form).
- `python3.10 scripts/check_architecture.py --mode strict` → exit 0, no `botsite/`
  findings.
- End-to-end smoke (no DSN set): app boots, `GET /submit` 200 + dormant notice,
  `POST` dormant → friendly 503, honeypot → 303 thank-you, **no `disbot` import**.

## ⚑ Self-initiated
None beyond the in-fence build — this was an assigned ultracode unit. The one
out-of-fence touch (the stale `test_app.py` stub assertion) is a required consequence of
filling the stub, flagged above, not a self-initiated feature.

## 💡 Session idea
**A `check_botsite_templates.py` guard that asserts every `botsite/templates/*.html`
extends `base.html` and that any route-rendered template referenced by `app.py`/router
modules exists on disk.** P1 deliberately wires routes whose templates land in later
units (P2/P3), so a typo'd template name or a missing `{% extends %}` would only surface
as a 500 at request time in production — a cheap stdlib AST+regex check would catch it in
CI, mirroring the existing `check_dashboard_data`/freshness guards. Worth having once the
bot site has its full template set; dedup-checked against `scripts/` — no equivalent
exists today.

## ⟲ Previous-session review
The foundation session (S1+S2+P1, #1109) did this **exceptionally well**: it left
`submit.py` as a documented stub with an explicit "Contract for P4" block naming the
export, the field list, and the migration — P4 was almost pure execution because of it.
That stub-with-contract pattern is the model for every disjoint-unit handoff.
**One concrete improvement it surfaced:** the stub's own P1 test
(`test_submit_router_is_mounted_but_stub`) hard-asserted the empty-router state, which
*by construction* must break the moment the owning unit (P4) fills it — so the foundation
session shipped a test guaranteed to fail its successor. **Workflow improvement:** when a
foundation unit ships a stub that a *named later unit* will fill, its test should assert
the **seam** (router is mounted / importable), not the **emptiness** (`routes == []`) —
the latter is a self-invalidating assertion that forces an out-of-fence edit on the very
unit it's handing off to. Cheap rule for the decomposition playbook
(`docs/planning/…-plan.md` §5 / the ultracode brief): *stub tests assert the contract,
never the placeholder's hollowness.*
