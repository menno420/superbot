# Session 2026-07-09 — console.json shape contract (superbot half)

> **Status:** `complete` — PR #1884, the producer half of the cross-repo
> console.json contract; the consumer half ships as a companion menno420/websites PR.

## What I did

Executed the `💡 Session idea` from `.sessions/2026-07-09-kl6-console-telemetry.md`
(PR #1883): the committed `botsite/data/console.json` is rendered by TWO repos —
superbot's own botsite console (`botsite/console/console.js`) and the **websites**
repo's dashboard `/console` page (fetched over raw.githubusercontent.com) — but
nothing pinned the shape both sides assume, so a producer-side family/field rename
silently blanks the consumer (the BUG-0022 desync class). Now it's pinned:

- **`botsite/data/console_data_contract.json`** — the committed, **versioned**
  shape contract (the existing `site_data_contract.json` pattern applied to this
  feed): `version` + `top_level` families + guaranteed fields per record
  (session / ideas / bugs / bug_open / bot_changelog / telemetry /
  telemetry_outcome / meta). Changing this file (and bumping `version`) is the
  explicit, reviewable act of changing the cross-repo contract.
- **Exporter** (`scripts/export_dashboard_data.py`): `build_console_subset` stamps
  `meta.schema_version = CONSOLE_SCHEMA_VERSION` into every emitted feed;
  `CONSOLE_CONTRACT_FILE` pins the contract path; the constants block documents
  the two-consumer reality (the #1883 context-delta gap, now pointed to in source).
- **Checker** (`scripts/check_dashboard_data.py`): new `check_console_subset`
  (`--console` CLI flag), mirroring `check_site_subset`, all fail-closed:
  producer-constants⇄contract **parity** (edit one without the other = red),
  top-level families **exact both directions** (extra = leak class, missing = the
  consumer-blanking class), `meta.schema_version` == contract `version`, and
  per-record guaranteed-field whitelists (sessions/telemetry rows exact incl. the
  nested `outcome`; meta/ideas/bugs/open-bugs/changelog subset).
- **Tests** (+13): 12 checker tests — including the **CI-enforcing**
  `test_committed_console_json_passes_contract` over the committed file — plus an
  exporter test pinning `meta.schema_version` to the contract file's `version`.
- `console.json` regenerated (`--targets console`; now carries
  `meta.schema_version: 1` + this session's telemetry row).

**Consumer half (companion PR in menno420/websites):** pinned contract copy +
render-time schema-version check on the dashboard `/console` page. Reading the
consumer against the new contract immediately surfaced a live defect there: the
console template treats `ideas`/`bugs` as **lists** (`|length`) while the feed
ships **dicts** (`{total, by_status, …}`) — its stat tiles show dict-key counts.
Fixed in the websites PR; exactly the class this contract exists to catch.

**Gates:** `check_quality.py --check-only` green · `check_architecture` untouched
(no `disbot/`) · `tests/unit/scripts/` 34+40 passed · `tests/unit/botsite/` 34
passed, 4 skipped · `check_dashboard_data --console` OK ·
`check_generated_artifacts_fresh` OK (4 fresh) · `check_current_state_ledger
--strict` exit 0 (benign newest-merge lag only) · full suite = CI (auto-merge
armed on green at PR open).

## Context delta

- **Needed but not pointed to:** which task_class values are legal for a
  `telemetry/model-usage.jsonl` row — the 8 Q-0248 classes live only in the kit
  repo's founding plan (§4.2/§5.2), not in superbot's `telemetry/README.md`,
  which says "the 8 Q-0248 classes verbatim" without listing them.
- **Pointed to but didn't need:** nothing notable.
- **Discovered by hand:** loading `check_dashboard_data.py` standalone via
  `importlib` without registering it in `sys.modules` first breaks its `Issue`
  dataclass on 3.10 (`_is_type` reads `sys.modules[cls.__module__]`); the repo's
  `_load_module` convention registers first for exactly this reason.
- **Decisions made alone:** contract file named `console_data_contract.json`
  (sibling symmetry with `site_data_contract.json`) rather than the idea's
  sketched `console.schema.json`; version surfaced as `meta.schema_version`
  inside the feed (no new top-level family, so no consumer sees an unknown key);
  sessions/telemetry rows enforced **exact** (producer builds them by whitelist
  comprehension) while dict families are subset-checked; contract-vs-producer
  parity lives in the checker (not exporter import time) so a broken contract
  file can never make the exporter itself unimportable.

## 🛠 Friction → guard

None new this session — the wrong-shape consumer defect found in websites is
itself the class this session's guard now catches, and the websites-side fix +
fixture correction ship in the companion PR. (No checker lied; no workflow slip.)

## 💡 Session idea

**Extend the pinned-feed-contract pattern to `dashboard.json`** — the websites
dashboard renders ~12 pages off the big feed with no contract at all; the console
contract proves the mechanism (producer parity + fail-closed checker + consumer
version check) and its first consumer-side pass caught a live defect, so the
bigger surface is the obvious next pin. Captured with full shape in
`docs/ideas/pinned-feed-contract-for-dashboard-json-2026-07-09.md` (+ README
index entry). Dedup-grepped `docs/ideas/` — the nearest neighbours
(`dashboard-registry-coverage-check`, `generated-artifact-freshness-umbrella`)
cover registry coverage and freshness, not shape.

## ⟲ Previous-session review (kl6-console-telemetry, #1883)

Strong session: whitelist-by-construction on the new telemetry family, honest
declared-vs-real lane discipline, and the `merge=union` guard shipped for a
conflict class it *predicted* rather than suffered. Its best output was arguably
the session card itself — the context-delta note ("nothing superbot-side mentions
the second consumer of console.json's shape") plus a precisely-shaped 💡 idea made
this session executable with near-zero re-discovery. One improvement it surfaces:
that context-delta observation and the idea were the *same fact* written twice,
and the cheap in-scope fix (a one-line "two consumers" pointer in the exporter's
constants block) shipped with neither — it waited a session for this PR. Concrete
workflow improvement: when a context-delta "needed but not pointed to" item is a
one-line source-comment fix, ship the pointer in the same session instead of only
filing it; the session-close skill could ask exactly that question.

## 📄 Documentation audit

- `check_current_state_ledger.py --strict` exit 0 (20 merged PRs newer than
  marker #1861 = benign newest-merge lag; reconciliation due at #1890 records
  them — this PR included).
- `check_docs --strict` green (new idea file reachable via the README index).
- Durable homes: the two-consumer fact + contract mechanics now live in source
  (exporter constants block, checker docstring, the contract file's `_comment`);
  the websites-side pointer ships in the companion PR's docs. Nothing left only
  in chat.

## 📤 Run report

- **Did:** pinned the console.json cross-repo shape contract (contract file +
  exporter schema_version + fail-closed checker + tests) · **Outcome:** shipped
- **Shipped:** #1884 — `console_data_contract.json`, `check_console_subset`
  (`--console`), `meta.schema_version`, +13 tests, feed regenerated
- **Run type:** `manual` (coordinator-dispatched kit-lab cross-repo improvement)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (executes the #1883 session idea as dispatched;
  the new idea filed this session is captured, not built)
- **↪ Next:** websites companion PR (pinned copy + render-time check + the
  dict-vs-list console fix); then consider the dashboard.json contract idea

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1884, auto-merge on green) |
| CI-red rounds | 0 (born-red card gate only) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (dashboard.json pinned-feed contract) |
| Ideas groomed | 1 (#1883's console-contract idea → implemented, this PR) |
