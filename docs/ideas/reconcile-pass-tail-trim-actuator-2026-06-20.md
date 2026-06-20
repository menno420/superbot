# Idea — a tail-trim actuator for the `current-state.md` ▶ Next action callout

> **Status:** `ideas` — session idea (2026-06-20, Q-0089, from the band-#1200 reconciliation pass).
> Workflow/tooling. The deterministic complement to the (now-shipped) Recently-shipped trim actuator,
> aimed at the *other* accreting structure every pass grows.
> **Subsystem:** none

## The observation

Every Q-0107 reconciliation pass prepends one "**Nth Q-0107 PASS DONE …**" sentence to the
`current-state.md` ▶ Next action callout. Seventeen passes in, that callout is a single enormous
paragraph of mostly-*consumed* band history — it fights its own "read THIS line" purpose, which is the
exact standing Q-0102 finding the band-#1170 pass restated ("each pass should aggressively prune consumed
band-history out of the live ▶ Next action into its pass record … a dedicated trim is itself a good ungated
session"). Each pass takes "a first cut" by hand and the bloat keeps winning.

The Recently-shipped *list* already got its deterministic fix this band (`scripts/trim_recently_shipped.py`,
#1181). The ▶ Next action *callout* has no equivalent — it is still a per-pass judgment call, which is why
it never actually shrinks.

## The idea

A small stdlib actuator (or a `--callout` mode of the existing `trim_recently_shipped.py`) that:

1. finds every "`<Ordinal> Q-0107 PASS DONE (…, band-#NNNN, …)`" segment in the ▶ Next action callout;
2. keeps the **two** most recent (the live line + one prior for continuity) and moves each older segment's
   prose into its already-existing per-band pass record (`reconciliation-pass-*-bandNNNN.md`), which is the
   canonical archive for exactly that history;
3. leaves a one-line pointer in the callout (`— older passes: see their per-band pass records`);
4. runs as a dry-run diff first (like the Recently-shipped trimmer), never deletes, idempotent.

This turns the documented "aggressive prune" from a vibe into a number-bounded, reviewable step — the same
detector→actuator pattern that worked for the ledger.

## Caveat (Q-0105)

Disposable dev tooling. The callout is hand-written prose with inline links, so the segment boundaries are
fuzzier than the Recently-shipped bullet list — prototype on `--check` and confirm the moved prose lands
intact a couple of passes before trusting `--apply`. **Heed BUG-0020:** the sibling trim actuator mis-wrote
its floor pointer by matching stray `#N` in prose on first real use, so any new pass-record-writing helper
must ground-truth its output and ship a self-test for its own fragile spot in the same PR.
