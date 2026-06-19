# 2026-06-19 — Website two-site split: serial foundation (S1 + S2 + P1)

> **Status:** `complete`

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

## Shipped (PR #1109)

All three foundation units, in order `S1 → {S2, P1}`:

- **S1** — `scripts/export_dashboard_data.py` emits both `dashboard.json` + the new
  `botsite/data/site.json` (`--targets`, both by default). `build_site_subset()` is
  redaction-by-construction (top-level keys *exactly* `{meta, counts, catalogue,
  commands, bot_changelog}`; catalogue-only counts; value-free commands). Folded in the
  `bot_changelog` parse + seeded `docs/bot-changelog.md`. Registered `site.json` in
  `check_dashboard_data.check_site_subset` (fail-closed whitelist + counts) and
  `check_generated_artifacts_fresh` (freshness). Tests in
  `tests/unit/scripts/test_export_dashboard_data.py` (+ the two guard test files).
- **S2** — `botsite/migrations/001_submissions.sql` (one canonical DDL, separate
  dashboard-owned Postgres) + `botsite/submissions_db.py` (INSERT-only) +
  `dashboard/submissions_db.py` (SELECT+UPDATE). Share only the table contract, no
  code. Tests run with no live Postgres (pure helpers + a fake asyncpg connection).
- **P1** — `botsite/{__init__,app,data_loader,submit}.py` + `Procfile` +
  `requirements.txt` + `templates/{base,index}.html` + `README.md` +
  `tests/unit/botsite/test_app.py`. `app.py` wires every route up front; `/submit` is
  a mounted empty-stub router; secret-free; no `static/`.

**Verification:** `check_quality.py --full` green (formatters + `mypy disbot/` + full
pytest **10,895 passed, 37 skipped**); `check_architecture.py --mode strict` exit 0;
no web→`disbot/` import. Verified locally that the app boots and `/` renders without
loading `disbot`, and that the whitelist guard fails closed on an injected `env_usage`
key.

## Decisions made alone (ratify)

- **`commands` subset `cooldown` = `null`.** The AST command scanner
  (`scan_commands.py`) does not statically resolve runtime cooldown decorators, so the
  whitelisted `cooldown` field is emitted `None` rather than fabricated. `name` /
  `aliases` / `category` / `permissions` (= subsystem `visibility_tier`) / `usage`
  (= the scanner's `brief`) are populated honestly. A later unit can enrich `cooldown`
  if the scanner learns to read `@commands.cooldown(...)`.
- **Raised the `check_docs` top-level-docs ratchet 19→20.** The plan pins
  `docs/bot-changelog.md` at the docs root; it is a genuine top-level *content* peer
  (a durable user-facing ledger alongside `current-state.md` / `roadmap.md`), so this
  is a sanctioned raise in the same class as the 2026-06-14 `repo-sector-map` raise —
  documented inline. (The alternative, hiding it in a subdir, would fight the plan's
  pinned path and the README/producer references.)
- **`site.json` whitelist enforced in three places.** The producer (`build_site_subset`
  raises on a stray key), `check_dashboard_data.check_site_subset` (error-severity,
  fail-closed), and `check_generated_artifacts_fresh.drift_site_json`. Triple-guarding
  the redaction boundary is deliberate — it is non-negotiable #1 of the plan.

## 💡 Session idea — public-data-contract *field-level* snapshot test

S1 guards the `site.json` **top-level** keys (fail-closed). The next leak class is
*within* a whitelisted family: a producer change that adds a new **field** to
`commands` or `catalogue` that turns out to be sensitive (e.g. a per-guild value, an
internal id) would pass the top-level whitelist silently. **Idea:** a tiny snapshot
test that pins the *exact set of leaf field names* per public family (a committed
`site_contract.json` of `{family: sorted(field_names)}`), so any new field — safe or
not — trips the test and forces a conscious "is this field public?" review before it
ships. Cheap, stdlib, extends redaction-by-construction from keys to leaves. (Dedup:
no existing idea covers field-level public-contract pinning — only the top-level
whitelist this PR adds.) Worth having because the whole split rests on non-negotiable
#1, and the *field* boundary is the one the current guard doesn't cover.

## ⟲ Previous-session review (#1107 — the §5 disjoint-tighten)

**Did well:** #1107 (the pre-ultracode plan tighten) is *why this build had zero write
conflicts* — it folded the P1/P2/P4 `app.py` overlap and the S1/P3 producer overlap
into single owners and pinned the whitelist keys, so I built §5 literally as written
with no "decide at build" ambiguity. That is the planner-feeds-builder loop working
exactly as intended. **Could have been sharper:** §5 named the `commands` whitelist as
`name/aliases/category/cooldown/permissions/usage` without noting that the existing AST
scanner produces none of `cooldown`/`permissions`/`usage`/`category` directly — I had
to reverse-engineer the honest mapping (join to the subsystem catalogue; `cooldown`
unscannable). **System improvement:** when a plan pins an *output field list*, it
should cite the *source field* each maps from (or flag "needs a new scanner field"), so
the builder doesn't discover a fabrication risk mid-build. I captured the honest mapping
in `export_dashboard_data` comments + the session-idea field-contract test so the gap is
now visible to the next agent rather than tribal.

## 📨 Documentation audit (Q-0104)

- `check_docs --strict` → green (the new `docs/bot-changelog.md` is badged + reachable;
  README links resolve; ratchet at 20).
- `check_current_state_ledger.py --strict` flags PRs #1096/#1097/#1100–#1103 missing
  from `current-state.md § Recently shipped` — **pre-existing benign newest-merge lag**
  (all *newer* than the `Last reconciliation pass: #1094` marker; the convention + the
  Q-0166 carve-out say the next reconciliation pass records these, and Q-0124 says a
  build session should not divert into a docs pass). Not this session's drift; flagged
  in the run report for the next pass. This PR (#1109) is itself newest-merge lag the
  next session/ledger entry will record.
- New owner-relevant decisions: none requiring a router Q (the build executes the
  already-decided plan §5; the ratchet raise + `cooldown=null` are recorded above and
  in-code, not product-intent forks).

## Context delta

- **Needed but not pointed to:** the command-field provenance (which `site.json`
  command fields map from which scanner fields) — reverse-engineered from
  `scan_commands.py`; now in `export_dashboard_data` comments. Also: the `check_docs`
  top-level-docs ratchet exists and a new top-level doc trips it — not surfaced by the
  `new-doc` route until CI fails; worth a one-liner in the docs-authoring orientation.
- **Pointed to but didn't need:** CodeGraph — this was a contained, plan-recipe build
  (new files in a known shape), so `context_map` + grep + the plan §5 file list carried
  it; the symbol graph would have been overhead (matches the CLAUDE.md "right tool by
  task size" guidance).
- **Discovered by hand:** `check_architecture.py` only scans `disbot/` (so `botsite/`
  is never arch-checked — the web→`disbot/` ban must be enforced by the app's own test,
  which I added); the dataclass-in-an-importlib-loaded-module needs `sys.modules`
  registration *before* exec (else `__module__` resolves to `None`) — the repo's
  `_load_module` already handles this, but a bare `importlib` loader doesn't.
- **Most-helpful one change:** a plan convention that an output-field whitelist cites
  each field's *source* (executed as the session-idea field-contract test + in-code
  comments).

## 📤 Run report

- **Did:** built the website two-site-split serial foundation (S1 data producer +
  public `site.json` subset, S2 submissions store, P1 bot-site app) end-to-end ·
  **Outcome:** shipped
- **Shipped:** #1109 — S1 + S2 + P1 (`botsite/` new service skeleton, `site.json`
  producer + redaction guards, submissions DDL + two helpers). Auto-merge armed; merges
  on green.
- **Run type:** `manual` (owner-dispatched ultracode build run)
- **⚑ Owner decisions needed:** `none` (executes the already-locked plan §5 / Q-0178/Q-0179)
- **⚑ Owner manual steps:** at rollout — provision the **2nd Railway service** (Root
  Directory = `botsite`), the **dashboard-owned submissions Postgres** + apply
  `botsite/migrations/001_submissions.sql`, and set `SUBMISSIONS_DB_DSN` (INSERT-only
  role on the public site, full role on the dev site). All dormant-by-default until
  then — nothing deploys-live without it (plan §6).
- **⚑ Self-initiated:** `none` (owner-dispatched build of the approved plan; the ratchet
  raise + `cooldown=null` are in-scope build decisions, recorded above)
- **↪ Next:** the parallel back-half units P2 (reference templates) · P3 (changelog +
  status templates) · P4 (submission intake — fills `botsite/submit.py` + copies the
  limiter) · P5/P6 (dev-site moderation + GitHub mirror) · P7/P8 (redaction-audit +
  deploy docs) — all file-disjoint, fan out now that this foundation lands.
