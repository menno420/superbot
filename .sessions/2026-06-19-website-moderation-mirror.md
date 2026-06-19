# 2026-06-19 — Website two-site split: P5 moderation UI + P6 GitHub-issue mirror

> **Status:** `complete`

Ultracode fan-out units **P5 + P6** of the website two-site-split
(`docs/planning/website-two-site-split-plan-2026-06-19.md` §5, §2.3, §4.3), built on the
merged foundation (`dashboard/submissions_db.py`, #1109). End-to-end: code + tests +
verification, on the owner-gated dev-site side of the split. Web tier never imports
`disbot/`.

## Shipped (PR #1118)

- **P6 — `dashboard/github_mirror.py`** (+ `tests/unit/dashboard/test_github_mirror.py`,
  12 tests): a single least-privilege, idempotent GitHub-issue-create client. Given an
  approved submission it creates **one** issue in `menno420/superbot` from the matching
  `.github/ISSUE_TEMPLATE/` shape (bug → "Where did it happen?"/Report; suggestion →
  Proposal) + the matching label (`bug` / `enhancement`). Reads `GITHUB_ISSUE_MIRROR_TOKEN`
  from env (dev site only); the repo target is **hardcoded, never env-redirectable**;
  untrusted user input is **HTML-escaped** into the issue body; `is_configured()` makes it
  dormant-by-default. Built/tested against a mocked `httpx` — no live token, no network.
- **P5 — dev-site moderation UI:**
  - `/admin/moderation` GET + `/admin/moderation/{id}/approve|reject` POSTs in
    `dashboard/app.py`, **owner-gated** (restricted to `BOT_OWNER_USER_ID`, read from env —
    `_bot_owner_id` / `_is_bot_owner` — to preserve the web-tier decoupling rule; same id +
    default as `disbot/config.py`, kept in sync by env, never by import). CSRF + a dedicated
    `_MODERATION_LIMITER` reuse the existing dashboard machinery. **Registered before
    `/admin/{guild_id}`** so the literal path is not shadowed (regression-tested).
  - `dashboard/templates/moderation.html`: lists `pending` via `submissions_db.list_pending`;
    all user input rendered **escaped** (Jinja autoescape); submissions never shown publicly;
    honest dormant ("set this up") + owner-only + mirror-disabled states.
  - `dashboard/templates/base.html`: owner-only **Moderation** nav link gated on `is_bot_owner`
    (added to `session_context`).
  - `tests/unit/dashboard/test_moderation.py` (15 tests).
  - **approve** = guarded sequence `create_issue` → `attach_issue_url` → `set_status('approved')`
    (row stays `pending` if the mirror fails → owner retries; idempotent on double-click via the
    "still in pending list" guard + the URL-IS-NULL / status='pending' DB guards). **reject** =
    `set_status('rejected')`.

## Verification (green)

- `python3.10 -m pytest tests/unit/dashboard/` → **104 passed** (27 new).
- `python3.10 -m mypy dashboard/` → **Success, no issues** (8 files).
- `python3.10 scripts/check_quality.py --check-only` → **All checks passed ✓ (exit 0)** — only
  the pre-existing 17 `views/ai/` `edit_in_place` warn-only findings.
- `python3.10 scripts/check_architecture.py --mode strict` → **exit 0** (no `dashboard/` findings;
  only pre-existing `disbot/` `[known]` warnings).
- `python3.10 scripts/check_quality.py --full` → 10922 passed before the final fmt fixes; re-run
  formatters green after.
- Decoupling re-confirmed: no `disbot` import in `dashboard/github_mirror.py` or `dashboard/app.py`.
- Merged `origin/main` (was 6 behind from parallel agents) — clean, no collision (my code files are
  exclusive; siblings only touched `dashboard/README.md` + `dashboard/data/dashboard.json`).

## Decisions made alone

- **Owner-gate reads `BOT_OWNER_USER_ID` from env in the dashboard** (not imported from
  `disbot.config`). The web tier must not import `disbot/` (architecture invariant), and `auth.py`
  / `submissions_db.py` already read their config from env — so the owner id follows the same
  pattern, with the **same hardcoded default** (`340415158583296000`) as the bot, kept in sync by
  env not import. A mis-set/blank value fails **closed** (matches nobody).
- **GitHub repo target is hardcoded** (`menno420/superbot`), not env-driven — a mis-set env must
  never be able to redirect approved public submissions into another repository.
- **Approve is a guarded mirror-first sequence**: the row is only flipped to `approved` *after* a
  successful issue create + URL store, so a GitHub failure leaves it `pending` for retry. Combined
  with `list_pending`-membership + the foundation's URL-IS-NULL / status='pending' guards, a
  double-click cannot double-file (plan §4.2 idempotency, realized without a new DB column).
- **Issue body HTML-escapes** the submitted free text even though GitHub renders markdown (not live
  HTML) — faithful rendering + no raw-HTML surprise, cheap, and matches the moderation template's
  escaping.

## Flagged for maintainer (known limits)

- **No live round-trip yet** — the mirror is verified only against a mocked `httpx`, and moderation
  against monkeypatched `submissions_db`/`github_mirror`. The real path needs the owner to (1)
  provision the dashboard-owned Postgres + apply `botsite/migrations/001_submissions.sql`, set
  `SUBMISSIONS_DB_DSN` (full role) on the dev site; (2) mint the fine-grained PAT (repo-scoped,
  Issues: R&W only) as `GITHUB_ISSUE_MIRROR_TOKEN` on the dev site; (3) confirm `BOT_OWNER_USER_ID`.
  Env names + scopes are documented in `docs/operations/env-vars.md` (P8).
- **Owner-gate is single-id** — exactly `BOT_OWNER_USER_ID` sees moderation, matching the bot's
  single-owner model. If a co-owner ever needs it, that's a deliberate later change.

## Context delta

- **Needed but not pointed to:** the **FastAPI route-registration-order** gotcha — `/admin/moderation`
  would be shadowed by the dynamic `/admin/{guild_id}` route if registered after it. Not in any
  dashboard doc; reverse-engineered from the route table. Worth a one-line note in
  `docs/operations/botsite-deploy.md` or the dashboard README for the next web-route author.
- **Needed but not pointed to:** `check_quality.py` **excludes `tests/`** from black/isort/ruff
  (CLAUDE.md says CI does, and the script mirrors it via `_BLACK_EXCLUDE`/`_RUFF_EXCLUDE`). A manual
  `black dashboard/ tests/...` produces false "would reformat" noise + `S101` ruff errors on test
  files — trust `check_quality.py`, never hand-run a formatter over `tests/`. (This is in CLAUDE.md's
  CI-parity section; re-confirmed the hard way.)
- **Pointed to but didn't need:** CodeGraph — this was a contained, single-module + single-file-edit
  build; `context_map`-style reading of the existing `dashboard/app.py` + `submissions_db.py` +
  `test_app.py` patterns carried it, exactly as the "reach for the right tool by task size" guidance
  predicts.
- **Discovered by hand:** the dev-site templates do **not** inject CSRF via a context processor; the
  per-guild editor mints it on demand and passes `csrf_token` explicitly per render. Mirrored that
  for moderation (mint in the GET, persist the session, validate in the POST).

## 💡 Session idea

**A `check_route_order.py` guard (or a `dashboard`/`botsite` test) that flags a literal route
registered *after* a same-prefix dynamic route that would shadow it** (e.g. `/admin/moderation` after
`/admin/{guild_id}`). The shadowing is silent — the literal just never matches — and as the web tier
grows (the bot site adds `/commands`, `/features`, … plus a future `/manage` service) this is an easy,
invisible footgun. A tiny AST/`app.routes`-order check would catch it at CI time. Dedup-checked
`docs/ideas/` + roadmap: not present (closest are web-tier *centralization* + redaction ideas, a
different concern). Worth having — cheap, prevents a whole class of "route 404s for no reason" bugs.

## ⟲ Previous-session review

Reviewing **`2026-06-19-website-deploy-redaction-docs.md` (P7+P8, PR #1113)** — the docs peer of this
fan-out wave. **Did well:** it verified the §4.1 redaction matrix against the *live* `dashboard/app.py`
routes rather than the plan's prose, and it pre-documented my P5/P6 env (`GITHUB_ISSUE_MIRROR_TOKEN`,
`SUBMISSIONS_DB_DSN`) + the moderation flow in `env-vars.md` / `dashboard/README.md` — so when I built
P5/P6 the durable doc homes already existed and I didn't have to (and per scope, couldn't) touch them.
That cross-unit foresight is exactly what makes a fan-out wave cohere. **Could improve:** the redaction
audit lists `/admin/moderation` as "audited against its P5 spec" — now that P5 *exists*, the audit row
is a spec reference, not a verified-against-code row; a follow-up should re-point it at the shipped
route + the owner gate. **System improvement it surfaces:** the redaction-audit doc should carry a
"last verified against commit `<sha>`" stamp per row (or at least per pass), so a reader can tell a
verified-against-code row from a verified-against-plan one — the same "generated vs live" freshness
honesty the plan applies to the bot site, applied to the audit doc itself.

## 📤 Run report

- **Did:** Built website-split units P5 (dev-site submission moderation UI) + P6 (GitHub-issue mirror), end-to-end with tests + verification. · **Outcome:** shipped
- **Shipped:** #1118 — P5 `/admin/moderation` (owner-gated approve/reject) + `moderation.html`; P6 `dashboard/github_mirror.py` (least-privilege, idempotent, mocked); 27 new tests; all checks green.
- **Run type:** `manual` (ultracode dispatch of P5+P6)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** provision the dashboard-owned Postgres + apply `botsite/migrations/001_submissions.sql`; set `SUBMISSIONS_DB_DSN` (full role, dev site); mint the repo-scoped Issues:R&W PAT as `GITHUB_ISSUE_MIRROR_TOKEN` (dev site only); confirm `BOT_OWNER_USER_ID` — then a live submit→approve→issue round-trip is the only unverified half (env names in `docs/operations/env-vars.md`).
- **⚑ Self-initiated:** none (P5+P6 were the dispatched task)
- **↪ Next:** the website-split back half is complete (S1.1/P2/P3/P4/P5/P6/P7/P8); remaining is owner provisioning/cutover (§6) + the deferred control-API security-review slice (§4.4 / §7.4).
