# Public-data-contract field-level snapshot test

> **Status:** `ideas` — a brainstorm capture, **not** a plan and **not** approval.
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
