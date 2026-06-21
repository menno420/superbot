# Public-data-contract field-level snapshot test

> **Status:** `historical` — **SHIPPED 2026-06-21** (dispatch run). The field-level
> redaction contract is live: `export_dashboard_data.SITE_FIELD_CONTRACT` pins the exact
> leaf fields per public family (`meta` / `meta.build` / `counts` / `catalogue` /
> `commands` / `bot_changelog`) and `check_dashboard_data.check_site_subset` fails closed
> on any un-vetted field within an allowed family — keys *and* leaves both fail closed, so
> the redaction contract is now total. See ▶ Outcome below.
> Session idea (2026-06-19, Q-0089), from the website two-site-split foundation build
> (PR #1109, units S1+S2+P1).
> **Subsystem:** none — the site.json redaction guard (export tooling).

## The gap

The foundation build (S1) guards the public `botsite/data/site.json` subset at the
**top-level key** boundary, three ways: the producer (`build_site_subset` raises on a
stray key), `check_dashboard_data.check_site_subset` (error-severity, fail-closed
whitelist), and `check_generated_artifacts_fresh.drift_site_json`. That is the strong
guarantee for non-negotiable #1 (the public site physically cannot carry a dev-only
*family*).

But the guard stops at the family boundary. The next leak class is **within** an
allowed family: a producer change that adds a new **field** to `commands` or
`catalogue` (say a per-guild value, an internal id, or a future `owner_only_note`)
would pass the top-level whitelist **silently** — the family is allowed, so nobody is
forced to ask "is this *field* public?".

## The idea

A tiny, stdlib snapshot test that pins the **exact set of leaf field names per public
family**. Commit a `botsite/data/site_contract.json` (or inline constant) of the shape
`{ "commands": ["aliases", "category", "cooldown", "name", "permissions", "usage"],
"catalogue": ["badges", "category", "description", "display_name", "emoji", "is_game",
"key", "tags"], "meta": [...], "counts": [...] }`. The test asserts every public
record's field set equals the pinned contract. Any new field — safe *or* not — trips
the test and forces a conscious "should this be public?" review + a contract bump
before it can ship.

## Why it's worth having

- The whole split rests on non-negotiable #1 (the public site never leaks). The
  *field* boundary is precisely the one the current top-level guard does **not** cover.
- It is cheap (stdlib, no new dep), disposable (Q-0105 — delete if it nags without
  catching anything real), and extends "redaction by construction" from keys → leaves
  with no runtime cost.
- It composes with the existing fail-closed whitelist: keys *and* leaves both fail
  closed, so the redaction contract is total.

## Disposition

Quick-win, decided-lane. Natural home: extend `tests/unit/scripts/test_export_dashboard_data.py`
(or a sibling) with the contract + assertion, and surface the contract in
`check_dashboard_data.check_site_subset` so the CLI guard covers it too. Relates:
`scripts/export_dashboard_data.py` (`build_site_subset`, `SITE_TOPLEVEL_KEYS`,
`SITE_COMMAND_FIELDS`) · `scripts/check_dashboard_data.py` · the website two-site-split
plan §2.2/§4.1 (the redaction boundary).

Dedup note: no existing idea covers field-level public-contract pinning — the closest,
[`website-two-site-split-2026-06-19.md`](./website-two-site-split-2026-06-19.md), is the
parent capture and only the top-level whitelist shipped in #1109.

## ▶ Outcome (2026-06-21, dispatch run)

Built as designed, generalized one step further than the original sketch (a registry over
*all* public families, not just a `commands` snapshot — the `commands` field whitelist
already shipped in S1.1, so this closed the gap for the rest):

- `scripts/export_dashboard_data.py` — new public field-contract constants
  (`SITE_META_FIELDS`, `SITE_META_BUILD_FIELDS`, `SITE_COUNTS_FIELDS`,
  `SITE_CATALOGUE_FIELDS` / `SITE_CATALOGUE_ENTRY_FIELDS`, `SITE_CHANGELOG_FIELDS`) and the
  `SITE_FIELD_CONTRACT` registry (family-path → allowed leaf fields, dotted paths pin
  nested dicts like `meta.build`). The catalogue projection now derives from the single
  `SITE_CATALOGUE_ENTRY_FIELDS` source (retired the duplicate `_SITE_CATALOGUE_FIELDS`).
- `scripts/check_dashboard_data.py` — `check_site_subset` now drives a generic
  within-family field whitelist off `SITE_FIELD_CONTRACT` (replacing the bespoke
  per-command block), with `_resolve_field_path` for dotted nested paths. Emits
  `site_field_not_whitelisted` (error) naming the offending family + fields.
- Tests: per-family fail-closed cases (catalogue / nested `meta.build` / changelog) plus
  the commands case retargeted to the new code; export-side parity tests that the contract
  covers every `SITE_TOPLEVEL_KEYS` family and is a superset of the live build.

Q-0105 reliability note: stdlib, no new dep, runs in CI through the existing
`test_committed_site_json_passes_guard` / `test_live_site_subset_is_clean` pytest guards.
Disposable — delete `SITE_FIELD_CONTRACT` + its checks if it nags across sessions without
catching a real leak.
