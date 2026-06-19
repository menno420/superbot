# 2026-06-19 — Bot-site changelog + status pages (P3)

> **Status:** `complete`

Built unit **P3** of the website two-site split
([plan](../docs/planning/website-two-site-split-plan-2026-06-19.md) §5 + the "Site
identity & experience" brief + §3 freshness model) on the merged foundation
(S1+S2+P1, #1109/#1110). Exclusive-file build run — two templates + their test, no
`botsite/app.py` edit (the `/changelog` + `/status` routes were wired in P1).

## Shipped (PR #1116)

- **`botsite/templates/changelog.html`** — a curated, user-facing **timeline grouped
  by date** from `site.json.bot_changelog` (`{date, title, kind, summary}`). Kind
  tags (`feature`→New / `improvement`→Improved / `fix`→Fixed; neutral "Update" for
  untagged), an honest **"generated" freshness badge** (no live claim, §3), a friendly
  empty state. Surfaces **no raw internal PR numbers** as user-facing ids (brief);
  renders an optional outbound "Details →" link **only if** a future producer ever
  supplies a `url` field (future-proof, no coupling — the curated source has none today).
- **`botsite/templates/status.html`** — a slim **user trust band** from
  `site.json.meta.build`: online-as-of-last-deploy + build SHA / date / latest-change
  subject, with a prominent **"generated" badge** ("as of last deploy", **no real-time
  claim** — the public site never reads the bot's private control API, §3). Honest
  catalogue counts (commands/features/games), **never** server/user totals. Friendly
  "Status unavailable" empty state + slate dot when build meta is absent.
- **`tests/unit/botsite/test_changelog_status.py`** — 10 `importorskip`-guarded tests:
  curated entries render (HTML-escaped via MarkupSafe), kind tags, the
  generated-not-live posture, **no-PR-number leak**, the date-grouping (same-date
  entries collapse under one heading, newest-first), no server/user totals, both
  friendly empty states.

## Verification

- `python3.10 scripts/check_quality.py --full` → **10904 passed, 37 skipped** (CI
  mirror, Python 3.10). `check_architecture --mode strict` → 0 errors.
- All 32 `tests/unit/botsite/` tests green (23 P1 + 10 new — one extra over the brief's
  ask to lock the date-grouping logic the committed data doesn't exercise).

## Context delta

- **Needed but not pointed to:** the **exact** `bot_changelog` record shape (no `url`
  field) and `meta.build` keys live only in `scripts/export_dashboard_data.py`
  (`parse_bot_changelog`) + the committed `site.json` — the plan describes the families
  but not the field names. Reading the producer's parser was load-bearing: the brief
  says "link out to GitHub release/PR", but the data has **no** link, so the honest
  build was an optional-link-if-present, not a fabricated one. (Worth a one-line
  "field shapes are in the producer's parser" pointer in the plan's P3 entry.)
- **Discovered by hand:** two render-time facts the test had to respect — (1) Jinja2
  autoescapes apostrophes to `&#39;` (decimal), so assert against `markupsafe.escape`,
  **not** `html.escape` (which emits `&#x27;`); (2) `data_loader.load_site_data` binds
  `DATA_FILE` as a *default argument*, so empty-state tests must wrap the loader to call
  it with a missing path, not monkeypatch the module attribute.
- **Pointed to but didn't need:** CodeGraph / the heavy arch-rule reading — this was a
  pure-template + test unit in the (arch-unchecked) web tier; `context_map` wasn't
  relevant either.
- **Decisions made alone:** (1) no fabricated changelog→PR link (the data lacks one;
  honesty over a guessed URL) — surfaced as an optional `url` hook; (2) the status
  page's "online" signal mirrors P1's base.html posture (a known build ⇒ green dot ⇒
  "online as of last deploy"), never a live ping; (3) added a 10th test beyond the
  brief to lock the multi-entry-per-date grouping. All reversible, template-only.
- **Weak point / flagged:** the pages are verified by unit render only — not by a real
  browser / Tailwind-CDN paint. They reuse the proven P1 base.html chrome, so layout
  risk is low, but a visual check at cutover is still worth it. Also: the "Details →"
  link path is unexercised until S1 (or a later unit) adds a `url`/release field to the
  changelog records — at which point a test asserting the link + the "no PR number"
  rule together would be good.

## 💡 Session idea

**A `botsite` template-contract test that asserts every `site.json` family a template
reads is one the whitelist/producer guarantees** — i.e. catch the inverse of the S1
redaction whitelist: not "did a private family leak *out*", but "did a template start
depending on a key the producer doesn't emit" (a silent empty-render regression). P3's
templates lean on `bot_changelog[].kind` and `meta.build.commit`; if a future producer
refactor renames a field, the page degrades to its empty state silently and CI stays
green. A tiny test that renders each template against the committed `site.json` and
asserts non-empty primary content (when the data is non-empty) would catch that drift —
the read-side mirror of the existing write-side whitelist guard. (Dedup-checked:
`docs/ideas/` has the redaction-whitelist and freshness-umbrella ideas, but none covers
the *template-reads-a-real-key* direction.) Filed here; small enough to fold into a
future botsite unit rather than a standalone idea file.

## ⟲ Previous-session review

The previous session (`2026-06-19-website-identity-and-fanout-enablers`, PR #1110) did
the right *sequencing* thing: it folded the owner's binding identity/experience vision
into the plan and added `botsite-ci.yml` **before** launching the fan-out, so units
like this one build to a settled spec and actually run in CI. Genuine remark: it
correctly resisted bundling the `web-ci.yml` centralization into the same PR (designed,
not rushed) — good restraint. What it could have done better for *this* unit: its plan
reshape detailed S1.1/P2 richly but left P3's data contract implicit — I had to read the
producer to learn `bot_changelog` has no link field, which directly shaped the "no
fabricated PR link" decision. **Concrete workflow improvement it surfaces:** when a plan
unit's deliverable says "render X from `site.json.Y`", the plan (or the unit's brief)
should name the **exact record fields** Y carries (or point at the producer function
that defines them) — a fan-out builder shouldn't have to reverse-engineer the data
contract from the generator to know whether a brief instruction ("link to the PR") is
even backed by data. This is the same class as the Q-0132 "doc claims that mirror code
must be CI-backed or stamped" rule, applied to plan↔data-contract drift.

## 📤 Run report

- **Did:** built website-split unit **P3** — the bot-site `/changelog` (curated
  date-grouped timeline) + `/status` (honest generated-only trust band) templates +
  tests, on the merged S1+S2+P1 foundation. · **Outcome:** shipped.
- **Shipped:** #1116 — P3 changelog + status templates (2 templates + 1 test; CI green
  10904 passed; auto-merge armed).
- **Run type:** `manual` (ultracode build dispatch on a named unit).
- **⚑ Owner decisions needed:** `none` (P3 had no open decisions; S1.1's three
  open decisions — `status` derivation / idea-link method / notes source — remain the
  previous session's surfaced items, not this unit's).
- **⚑ Owner manual steps:** `none` for P3. (Standing, unchanged: the bot site's Railway
  service + the cutover are owner steps per plan §6 — not triggered by this unit.)
- **⚑ Self-initiated:** `none` — this was a dispatched build of an existing planned unit
  (plan §5 P3); no idea was promoted to a plan/build unprompted. (The 10th test + the
  optional-`url` link hook are in-scope correctness, not a new initiative.)
- **↪ Next:** the rest of the back-half fan-out — **S1.1 → P2** (the interactive
  command/feature browser) ∥ **P4** (submit intake) · **P5/P6** (dev-site moderation +
  GitHub mirror) · **P7/P8** (redaction-audit + deploy docs). P3 is done.
- **Note (out of scope here):** `check_current_state_ledger.py --strict` reports
  pre-existing living-ledger drift (#1097–#1105 unrecorded) — older than this session
  and **not** in P3's exclusive file set; flagged for the docs-reconciliation routine /
  a manual docs session per the every-30-PR pass.
