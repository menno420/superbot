# Website two-site split — ultracode review-and-refactor report (2026-06-19)

> **Status:** `audit` — a dated, read-and-verify review of the website two-site-split build
> (PRs #1109, #1110, #1112, #1113, #1116, #1117, #1118, #1119). Source + merged PRs win over
> this record. Produced by the ultracode review pass on branch `claude/cool-feynman-cvqrbj`.

## Method

Every shipped file was read and **verified against source**, not trusted because CI was green.
The four hard invariants were proven (not assumed); the four known weak spots were exercised;
each defect was either **refactored** (with a test) in a file-disjoint unit or **flagged** for an
owner decision. Refactor units each pass `python3.10 scripts/check_quality.py --full` and
`python3.10 scripts/check_architecture.py --mode strict`.

## Hard invariants — all hold (proven)

| # | Invariant | How it was proven | Verdict |
|---|---|---|---|
| 1 | **Decoupling** — no web-tier file imports `disbot/` | `grep -rE '^\s*(import\|from)\s+disbot' botsite/ dashboard/` → none; `check_architecture --mode strict` exit 0; `test_app_does_not_import_disbot` | ✅ |
| 2 | **Redaction** — `site.json` carries only whitelisted families/fields; guard fails closed | Injected a private `env_usage` top-level key → `site_key_not_whitelisted` **error**; injected a per-command field → `site_command_field_not_whitelisted` **error**. Subset is built by construction from `SITE_TOPLEVEL_KEYS` + a defensive raise. | ✅ |
| 3 | **Security** — public site holds only the INSERT-only DSN; mirror token dev-only + repo-hardcoded + Issues-only; moderation owner-gated + CSRF + rate-limited; all user input escaped; submissions never public | `botsite/requirements.txt` has no httpx/OAuth; `github_mirror.REPO_OWNER/REPO_NAME` hardcoded (not env); `_moderate` re-checks owner → CSRF → rate-limit → store; templates render every submission field via `{{ }}` (autoescape on, zero `\|safe`); `/submit` only INSERTs `status='pending'` | ✅ |
| 4 | **Dormant-by-default** — no DSN/token/env ⇒ safe no-op | `submissions_db.is_configured()` / `github_mirror.is_configured()` gate every path; `/submit` shows a friendly 503; moderation shows a "set this up" state; lazy `asyncpg`/`httpx` imports | ✅ |

## Per-area verdicts

| Area | Files | Verdict | Notes |
|---|---|---|---|
| Bot-site app + routing | `botsite/app.py`, `data_loader.py`, `__init__.py`, `Procfile`, `requirements.txt` | **correct** | Single routing owner; safe empty-shape fallback; no `static/`. Minor: `load_site_data()` is read 2–3× per request (context processor + route + `_render`) — negligible for a committed-artifact marketing site; left as-is. |
| Submission intake | `botsite/submit.py`, `submissions_db.py`, `ratelimit.py`, `migrations/001_submissions.sql` | **refactored** | INSERT-only, honeypot + dual-window rate-limit + PRG. **Refactored:** `_clean` claimed to strip C0/C1 controls but the C1 block (0x80–0x9F, e.g. NEL/CSI) survived → now uses `unicodedata` `Cc` (keeps `\n`/`\t`), with a C1 regression test. |
| Producer + guard | `scripts/export_dashboard_data.py`, `check_dashboard_data.py` | **refactored** | Redaction-by-construction + fail-closed whitelist confirmed. **Refactored:** added the explicit `Subsystem:` tag mechanism to fix the `chain` heuristic mis-map (below). |
| Dev-site moderation + mirror | `dashboard/app.py` (`/admin/moderation`), `submissions_db.py`, `github_mirror.py`, `templates/moderation.html`, `base.html` nav | **correct** | Owner-gated at GET + every POST; CSRF (`hmac.compare_digest`); idempotency guards (`status='pending'` / `url IS NULL`); nav link owner-only. One **flag** below (approve double-file race). |
| Templates | `botsite/templates/*.html` | **correct** | Autoescape on, no `\|safe`/`markupsafe`; null `cooldown`/`use_cases`/`notes` render gracefully; honest "generated / as of last deploy" freshness badges; honeypot hidden; privacy note honest. The `_command_detail.html` **Notes block is the confirmed drop-in seam** for the future per-command feedback threads — no refactor needed. |
| Web CI | `.github/workflows/botsite-ci.yml` | **correct** | Runs `pytest tests/unit/botsite` + `mypy botsite/`; tool pins match the other 3 CI/dev locations (mypy 2.1.0 / pytest 9.0.3 / pytest-asyncio 1.4.0). Centralization **flag** below. |
| Test isolation | `tests/unit/{botsite,dashboard}/*`, `tests/support/web_app_loader.py` | **refactored** | The confirmed run-order CI bug (below). |
| Docs | `botsite-deploy.md`, `dashboard-redaction-audit.md`, `env-vars.md`, plan | **refactored** | Deploy + redaction docs accurate. **Refactored:** the `env-vars.md` Website-tier drift (below). |

## What was refactored (this pass)

1. **Test-isolation `sys.modules` collision (confirmed CI bug).** Both web services deploy with
   Railway Root Directory = their own folder, so each `app.py` imports siblings by **bare name**
   after a `sys.path` shim. In a single test process loading both apps, `submissions_db` /
   `ratelimit` (which exist in both dirs with different APIs) collided — the bot-site INSERT-only
   `submissions_db` (no `set_status`) shadowed the dashboard one, so `test_moderation.py` failed
   when it ran after `tests/unit/botsite` (order-dependent; green in isolation + the full-suite CI
   order, which is why CI stayed green). Fix: `tests/support/web_app_loader.load_web_app` isolates
   each load — own dir first on `sys.path`, evict only genuinely-colliding cached bare modules.
   Verified green in **both** orderings. Centralised the loader boilerplate across 7 fixtures.
2. **`botsite/submissions_db._clean` C1 hardening** (above).
3. **Idea→subsystem `chain` mis-map.** The slug heuristic surfaced the agent-workflow
   "executor self-chaining" idea as a "what's planned" teaser on the **Word-Chain game** commands
   (`chain`/`chainmenu`/`create`/`delete`/`list`/`setlimit`/`removelimit`) and marked them
   in-progress. Built the greenlit explicit `> **Subsystem:**` tag (header-only parse, prefer over
   heuristic, `none` sentinel for meta ideas); tagged the offending idea `none`. Verified the change
   is **surgical**: exactly those 7 commands flip to `finished`, nothing else.
4. **`env-vars.md` web-tier drift.** P8 added a hand "Website tier" section; the byte-equality
   freshness test then reddened main and #1119 deleted it, leaving three docs pointing at a missing
   section. Added an `END_MARKER` so the generated head and a hand-maintained tail coexist; both
   verifiers compare only the head; restored the Website-tier reference. Regen is idempotent.

## Flag-for-owner (decisions — not guessed)

1. **Moderation approve = a small double-file race.** `_moderate` (approve) does
   `list_pending` → `create_issue` → `attach_issue_url` → `set_status('approved')`. Two *concurrent*
   approves of the same row could both pass the still-pending check and create **two** GitHub issues
   (the DB idempotency guards prevent double-status/double-url, not double-issue). Risk is low (single
   owner moderator, CSRF + rate-limit). Options: (a) accept for v1 (recommended); (b) flip to a
   transient `mirroring` status before `create_issue`; (c) a DB advisory lock. **Decision: which?**
2. **Web CI matrix consolidation.** `dashboard-ci.yml` + `botsite-ci.yml` are near-twins; the
   centralization proposal designs one `web-ci.yml` matrix and an extracted auto-managed-PR predicate.
   The proposal itself says ship these as **focused PRs with both matrix legs verified green** before
   deleting the per-service files — higher blast-radius than this review PR should carry. **Left as a
   flagged focused follow-up** (recommended: do it; it's a clean win once both legs are CI-verified).
3. **Full idea→subsystem mapping.** This pass fixed the mechanism + the one confirmed false-positive.
   Correctly mapping all ~80 ideas (the `idea-to-cog-command-mapping` effort) is a deliberate,
   owner-paced batch effort — **not** done here. The heuristic remains the safe fallback for untagged
   ideas (title+status only, so a stray match is never unsafe — only mildly imprecise).

## References

- [`../planning/website-two-site-split-plan-2026-06-19.md`](../planning/website-two-site-split-plan-2026-06-19.md) — the build this reviews.
- [`dashboard-redaction-audit.md`](dashboard-redaction-audit.md) · [`botsite-deploy.md`](botsite-deploy.md) · [`env-vars.md`](env-vars.md) — the docs reconciled here.
- [`../planning/web-tier-centralization-proposal-2026-06-19.md`](../planning/web-tier-centralization-proposal-2026-06-19.md) — flag #2.
- [`../ideas/idea-subsystem-tag-on-ideas-2026-06-19.md`](../ideas/idea-subsystem-tag-on-ideas-2026-06-19.md) — the tag mechanism (refactor #3).
