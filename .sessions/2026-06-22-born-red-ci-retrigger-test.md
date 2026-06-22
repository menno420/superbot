# 2026-06-22 — Experiment: does a born-red PR re-fire CI on a second push?

> **Status:** `in-progress` — deliberately born-red CI-retrigger experiment (owner-directed).
> Tests whether the journal claim "a push to an existing PR branch does NOT fire
> `pull_request: synchronize` Code Quality runs" is still true after the `cancel-in-progress:
> false` CI-strand fix (#1267/#1275, 2026-06-22). Expected: the claim is now FALSE — the second
> push should fire a fresh Code Quality run on the new head SHA.

> **Run type:** `manual · owner-directed experiment`

## What I'm about to do

1. Open this PR born-red (this `in-progress` card fails `check_session_gate` → Code Quality red).
2. Push a second commit (flip this card section / add a note).
3. Observe whether a NEW Code Quality run appears on the second head SHA.

## Result

_(pending — recorded after the second push)_

## Second push marker

Second commit pushed to the open PR branch to test the `synchronize` trigger.
