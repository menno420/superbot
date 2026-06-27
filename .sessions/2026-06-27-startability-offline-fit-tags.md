# 2026-06-27 — Per-sector offline-fit startability tags (workflow improvement)

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did

Empty-fire dispatch. Acted on a **twice-flagged** self-audit observation (the Q-0102 reviews in the
2026-06-25 and 2026-06-26 session logs, which reached the "route it if it recurs once more" bar): only
the **S2** per-sector live-state file tagged its `▶ Next` startable items with an offline-fit phrase, and
that worked as a fast dispatch signal — but S1/S3/S5 didn't, so every autonomous dispatch run (this one
included — I confirmed it firsthand) burned orient-time rediscovering which startables are
offline-verifiable vs. needs-live-bot vs. owner-gated. Built the fix end-to-end as one coherent
docs+tooling PR (no runtime / `disbot/` change).

**PR #1482 — the offline-fit startability tag system.**

**Slice 1 — the tag convention + checker.**
1. A small per-item offline-fit tag vocabulary — `[offline]` (offline-verifiable + self-mergeable) /
   `[needs-live-bot]` (needs a running bot / runtime creds to verify) / `[owner]` (needs an owner
   decision/action) — applied to every `▶ Next` item across `docs/current-state/S1-bot.md`,
   `S2-btd6.md`, `S3-ai-memory.md`, `S5-ops.md`, each with a one-line legend under the heading. S4 is
   exempt (its `▶ Next` is a cadence-gated reconciliation pass, not a buildable menu). A tag reflects an
   arc's *next actionable* step (a shipped arc whose next move is a live walk is `[needs-live-bot]`).
2. `scripts/check_startability_tags.py` (Q-0105 provenance header + kill-switch, **not** CI-wired —
   ask-first) asserts each non-exempt sector's `▶ Next` block carries ≥1 recognized tag, so the
   convention can't silently drift back out. Presence check, not a brittle per-bullet parse.
3. Documented the convention in `docs/repo-sector-map.md` § "the offline-fit startability tag", next to
   the existing sector-level unattended-fit tag.

**Slice 2 — wired it into the dispatch tool (closes the loop / Q-0207 option (c)).**
`scripts/dispatch_menu.py --unattended` now reads each buildable sector's live-state file and surfaces a
new **"Concrete [offline] items"** section — the actual item to build per sector — so an empty-fire run
never needs to open the sector file by hand (the exact friction the 2026-06-26 review described). S5
(all `[owner]`) and S4 (exempt) correctly produce no offline pick.

Recorded the **rule-level** question (bless the convention as standing / leave disposable / fold into
the tool) as router **Q-0207 (DISCUSS)** rather than self-editing CLAUDE.md.

## Verification
- New tests: `tests/unit/scripts/test_check_startability_tags.py` (11, incl. guard-the-guard:
  removing a tag makes the checker fail) + 5 added to `test_dispatch_menu.py` (the offline-pick parsing
  reads the live S1/S2/S3 files, S5 has none, label-strip, block-stops-at-next-heading, the summary
  surfaces the new section). `check_quality.py --full` GREEN. `check_startability_tags.py` OK (4 sectors
  tagged, S4 exempt). Arch unaffected (no `disbot/` change).

## 💡 Session idea (Q-0089)
*Tag the roadmap's per-sector `▶ Now/Next` items with the same `[offline]`/`[needs-live-bot]`/`[owner]`
vocabulary, not just the current-state sector files.* Today the roadmap carries a **sector-level**
unattended-fit tag (🟢/🟡/🔵/🟠) and the current-state files now carry **item-level** offline-fit tags —
two homes, slightly different vocabularies. A future slice could unify them: one tag vocabulary, applied
once at item granularity on the roadmap (the dispatch source of truth), with the current-state files
linking rather than restating (the one-fact-one-home rule). Low urgency — the two layers don't conflict
today, and dispatch_menu now bridges them — but it would remove the dual-vocabulary seam. Genuinely tied
to this run's edit, not filler.

## ⟲ Previous-session review (Q-0102)
The previous run (2026-06-26 BTD6 eval-anchor coverage) did its best work in **disciplined
guard-the-guard verification** — it proved its new coverage/distractor guards non-vacuous by emptying the
allowlist and forcing a truth==distractor, confirming each fails against the drift it exists to catch. I
mirrored that here (the checker's `test_missing_tag_fails`). Its Q-0102 note is **what this run executed**:
it flagged that autonomous runs burn orient-time finding offline lanes and recommended propagating S2's
offline-fit tag — this run is the third occurrence and the build of that exact fix. **System improvement
this surfaces:** the self-audit loop worked as designed — a friction flagged twice, then built — but the
gap was *latency*: the observation sat for two runs as a routed note before a run acted on it. A cheap
upgrade would be for the Q-0102 ender to **promote a twice-flagged observation into the bug-book or a
`docs/ideas/` entry on the second occurrence** (not just re-note it in prose), so the next empty-fire run
finds it as a concrete startable rather than re-deriving it. Routed as an observation here, not a
unilateral rule edit.

## Doc audit (Q-0104)
The four sector live-state files + `repo-sector-map.md` are the durable homes of the convention; Q-0207
is the durable home of the rule-level question. `check_current_state_ledger --strict` lag is benign
newest-merge lag (recon is the docs-reconciliation routine's lane at #1500, not a manual dispatch's —
Q-0124). `check_docs --strict` + `check_consistency` green. No ledger/Recently-shipped edit needed (this
PR ships no new merged-PR fact yet; the next session/recon records #1482). Claim file deleted at close.

## 📤 Run report
- **Did:** built the per-sector offline-fit startability tag system (tags + checker + map doc + router
  Q) and wired it into `dispatch_menu --unattended`. · **Outcome:** shipped
- **Shipped:** #1482 — `[offline]`/`[needs-live-bot]`/`[owner]` tags on S1/S2/S3/S5 ▶ Next items +
  `check_startability_tags.py` + `repo-sector-map.md` convention + dispatch_menu "Concrete [offline]
  items" section; +16 tests.
- **Run type:** routine · dispatch
- **⚑ Owner decisions needed:** Q-0207 (DISCUSS) — bless the offline-fit tag convention as standing /
  leave it disposable / fold it fully into dispatch_menu (agent rec: bless + the dispatch_menu wiring,
  already built).
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated:** yes — promoted the twice-flagged self-audit observation (Q-0102 notes) into a
  built workflow improvement (PR #1482), no dispatch or owner ask; flagged here + routed as Q-0207.
- **↪ Next:** the sector ▶ Next offline-fit tags are now the fast dispatch signal — an empty-fire run can
  run `python3.10 scripts/dispatch_menu.py --unattended` and build a listed **Concrete [offline] item**
  directly (S1 Fishing open-world / Project Moon Slice A·B · S3 self-test walker harness). Bug-book:
  BUG-0009 newest-towers data-gated, BUG-0011 needs VPS repro, BUG-0019 #1 awaits an owner behavior
  decision — all stay OPEN.
