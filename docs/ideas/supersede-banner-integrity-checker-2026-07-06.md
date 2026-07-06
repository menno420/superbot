# Supersede-banner integrity checker (2026-07-06)

> **Status:** `ideas` — session idea (Q-0089), from the rebuild-consolidation session (PR #1770).
> Not approved for implementation.

## The problem

Consolidation passes create **supersede webs by hand**: this session alone stamped six docs with
"⚠ SUPERSEDED (by X)" banners and wrote a disposition table in the canonical plan naming what each
older doc still owns. Nothing enforces any of it. The known failure modes, all observed in this
repo's history:

- a doc is superseded in a successor's table but **its own header never gets the banner** (the
  design-spec header still claimed "amendments — now folded in" four days after the Gate-0 fold
  landed elsewhere — BUILD-PLAN §4.4 called it blocker-class and it was still unfixed at head);
- a banner names a successor that **doesn't exist** or was renamed (the "phantom handoff §F"
  class — two docs cited a section that was never written);
- a superseded doc **keeps its `plan` badge**, so `docs/planning/README.md`'s "Active" promise and
  the doc's own header disagree, and agents act from a dead plan.

## The checker (stdlib, `check_docs`-style)

For every doc containing a `SUPERSEDED` marker: (1) the named successor path resolves; (2) the
successor mentions/links the superseded doc back (the disposition-table handshake); (3) the doc's
`Status` badge is **not** `plan` (must be `historical`/`reference`/an annotated hybrid). And the
reverse pass: every row of a "Superseded / disposition" table in a `plan`-badged doc points at a
doc that actually carries the banner. Warn-first (Q-0105 header, disposable), promote to
`check_docs --strict` once proven.

## Why it's worth having

"Enforce, don't exhort" (Q-0132/Q-0194) applied to the one docs-drift class that reconciliation
passes keep re-finding by hand. The supersede convention is now load-bearing — the canonical plan
is only "the single source of truth" while the losers visibly point at it.
