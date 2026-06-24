# 2026-06-24 — Harden the help-nav attachment seam (forward-path regression pins)

> **Status:** `complete` — PR #1431; auto-merge armed; merges on green. Full CI mirror green
> (12,469 passed, 48 skipped, 2 xfailed; black/isort/ruff/mypy clean) + all checks passed.

> **Run type:** `routine · dispatch`

## What I did
Continuation of the same dispatch fire that shipped PR #1430 (the help-nav attachment seam, which
auto-merged cleanly). The seam has **6 render sites** that forward a hub's `help_nav_card`, but #1430
added a *behavioral* forward-path pin on only **one** (the navigation back-button). The two
**highest-traffic Help-discovery paths** — `HubChildButton` hub-child navigation and the Help category
**select** dropdown — relied on the accessor but had **no test that fails if the `attachments=` forward
is dropped**. A refactor removing the forward from either would have passed CI silently.

## Shipped (PR #1431) — tests only, no production change
- `tests/unit/views/test_hub_children.py` — `test_forwards_help_nav_card_as_attachment` (card-bearing
  child → `attachments=[card]`) + `test_cardless_child_clears_attachments` (navigate-away clears).
- `tests/unit/help/test_help_category_view.py` — `test_selecting_hub_forwards_help_nav_card`
  (selecting a card-bearing hub forwards `attachments=[card]` on the in-place edit).

The seam's three main user-facing nav flows (back-button #1430 · HubChildButton · category select) are
now all behaviorally guarded. The two secondary render sites (admin `_open_via_help_hook` cross-nav,
typed `!help <cat>` send) stay covered by the accessor unit tests but aren't behaviorally pinned —
lower-traffic; noted for a future pass rather than force-tested here.

## 💡 Session idea (Q-0089)
A **static seam-completeness guard** would generalise this: a test that greps every help-nav render
site (the call sites of `build_help_menu_view` results that `edit_message`/`send`) and asserts each one
also references `help_nav_attachments`/`help_nav_send_kwargs`/`help_nav_card`. That converts "we
remembered to behaviorally pin the busy ones" into "a *new* render site that forgets the forward fails
CI" — the same shape as the existing `test_every_visible_subsystem_cog_has_build_help_menu_view`
reachability guard. Dedup-checked — not in `docs/ideas/`; small, flagged for grooming (a static-AST
guard is more robust than per-path behavioral mocks, but needs care to enumerate the render sites).

## ⟲ Previous-session review (Q-0102)
Reviewed the immediately-prior slice in this same run (#1430, the seam itself). Did well: it chose the
non-viral view-attribute shape over the sketched `(embed, view, file)` triple, avoiding 47-hook churn —
the right call, and it documented *why* in the code. What it under-did (and this PR fixes): it shipped
6 render-site forwards but only **1** behavioral pin, leaning on the accessor unit tests for the rest.
Accessor coverage proves the helper works in isolation; it does **not** prove each call site actually
*calls* it — exactly the gap a "looks tested" seam hides. **System improvement (acted on here):** when
a change adds a forwarding helper threaded through N call sites, the same PR should pin at least the
high-traffic sites behaviorally, not just unit-test the helper — "the helper is correct" ≠ "every caller
uses it". This run did the second half; folding the instinct into the seam idea above (a static
completeness guard) would make it automatic.

## Doc audit (Q-0104)
Tests-only change; no doc/ledger surface touched (the seam's docs were de-staled in #1430). `check_docs`
unaffected. Ledger entries for #1430 + #1431 land via the next reconciliation pass (band-#1440), no
placeholder (Q-0052). No owner-decision / router change.

## 📤 Run report
- **Run type:** `routine · dispatch`
- **Shipped (this run, 2 PRs):** #1430 (help-nav attachment seam + XP hub consumer) → #1431 (forward-path
  regression pins on the primary Help-nav paths).
- **⚑ Self-initiated:** YES — both PRs. #1430 promoted the groomed help-nav-seam idea → build; #1431
  hardened it. No work order (Q-0172). Contained, reversible, tests-only for #1431.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (merges auto-deploy to Railway).
- **Next ▶:** seam **incremental adoption** (any card-bearing hub sets `help_nav_card` in its hook — no
  hub other than XP has a card *and* a Help path today, so this waits on a new card-bearing hub) · the
  static seam-completeness guard idea above · the two secondary render-site pins (admin / typed help) ·
  unrelated substantial S1 lanes (Project Moon runtime PR 1, botsite React PR 2) for a fresh session.
