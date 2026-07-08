# Supersede-banner integrity checker (2026-07-06)

> **Status:** `historical` — ✅ **IMPLEMENTED 2026-07-08 (PR #1846, Wave-1 lane B).**
> Shipped as `scripts/check_supersede_integrity.py` (warn-first, Q-0105 header) + a soft-check
> delegation in `scripts/check_docs.py` (findings surface on every session-close run) + unit
> tests (`tests/unit/scripts/test_check_supersede_integrity.py`). Promotion to
> `check_docs --strict` stays pending per the warn-first plan below.
> *(Originally: session idea Q-0089, from the rebuild-consolidation session, PR #1770.)*

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

## Follow-ups (tracked 2026-07-08, grooming pass on PR #1846)

Two future-conditional follow-ons from the implementing session, recorded here (the idea's
lifecycle home) with explicit triggers so a later session can act on evidence, not memory:

- **Promote to `--strict`.** *Trigger:* after **~5 sessions / reconciliation passes of clean
  warn output** (the Q-0105 proving period — no false positives, and no Q-0120 false-green
  where visible banner drift passed). Then: run `check_supersede_integrity.py --strict` in the
  `check_docs --strict` session-close/CI path and drop the "unverified" header clause. If the
  warn period instead shows noise, the header's own instruction applies — delete the checker.
- **Extend scope to `.sessions/` and mid-doc banners.** *Trigger:* **if warn-period output (or
  a reconciliation pass) shows real supersede drift in `.sessions/` cards or in mid-doc
  section-level banners** — both intentionally out of scope today (see the checker header:
  only header-block banners under `docs/` count). Don't extend speculatively: mid-doc
  `SUPERSEDED` markers (e.g. `docs/btd6/`) are section-level by convention and a naive
  extension would be all noise.
