# 2026-07-11 — Fix codex-final-review workflow YAML (broken since #1105)

> **Status:** `complete`

📊 Model: Fable 5 · coordinator-directed lane session (CI fix) · day

## What this session is about to do

Fix the born-broken `.github/workflows/codex-final-review.yml`: it has been invalid YAML
since its creating commit `bfe99084` (PR #1105, 2026-06-19) — the multi-line `--body` string
in the last step de-indents out of the `run: |` block scalar, so every trigger since has been
an instant "Invalid workflow file" failure (~2,808 runs, zero successes).

## What was done (PR #1995)

- **Root cause confirmed**: old lines 76–79 passed `gh pr comment … --body "@codex review\n\n$marker …"`
  as a multi-line shell string whose continuation lines sat at column 1. A line below the
  block-scalar indent terminates the `run: |` scalar, so YAML parsed `$marker Session card
  flipped…` as a mapping key → `could not find expected ':'` (line 78). The workflow **never
  parsed once** in its life; canonical failed run: 29156086075.
- **Fix (minimal)**: the comment body is now built with `printf '%s\n\n%s\n' …` into
  `"$RUNNER_TEMP/body.md"` and posted via `--body-file` — every line stays at block-scalar
  indent; body wording preserved verbatim (verified by simulating the `printf` locally — output
  is byte-identical to the intended `@codex review` + marker text). Triggers, job `if:` gate,
  checkout, `check_session_gate --require-ready-card` step, env, and the idempotency marker
  check are untouched. One behavior tweak: `concurrency.cancel-in-progress` `false` → `true`
  so rapid synchronize pushes cancel superseded runs instead of stacking.
- **Validation**: `python3.10 yaml.safe_load` clean on the fixed file **and** on all 17
  `.github/workflows/*.yml` (whole-dir sweep); actionlint not on PATH (noted, not installed).
  `check_quality.py --check-only` green; ledger + docs checkers green (see audit below).
- **Ledger**: #1995 entry added to `docs/current-state.md` ▸ Recently shipped.

## 💡 Session idea

**Workflow-parse guard: a unit test that `yaml.safe_load`s every `.github/workflows/*.yml`**
(e.g. `tests/unit/docs/test_workflows_parse.py`, ~10 lines) — this session's bug class
(a born-broken workflow file) survived **22 days and ~2,808 failed runs** because nothing in
CI parses workflow YAML; GitHub only reports the error *at trigger time*, and nobody reads
the Actions failure list. A parse test makes the next `codex-final-review.yml` un-mergeable
red in the same PR that introduces it (Q-0194 friction→guard, checker tier — free to ship).
Dedup: `docs/ideas/repo-consistency-linter-2026-06-17.md` is adjacent (repo-wide lint) but
does not cover workflow YAML parseability; no other idea file touches it.

## ⟲ Previous-session review

`2026-07-11-email-fleet-handoff.md` is a model handoff card — the "▶ NEXT SESSION — START
HERE" block with the owner-action queue is the clearest continuation contract in `.sessions/`
yet. The genuine miss it surfaces (not that session's fault, but visible from here): **an
entire fleet of review/night-review sessions ran while a workflow failed ~2,808 times over
22 days and none noticed** — red-run noise in Actions is invisible to the current review
workflows because nothing summarizes per-workflow failure rates. Concrete improvement: add a
"workflows with 100% recent failure rate" line to the `/fleet-review` (night-review) checklist
— zero-success workflows are always either dead-parse bugs (this one) or dead triggers, both
worth one line in a review.

## Documentation audit (Q-0104)

`check_current_state_ledger.py --strict` ✓ · `check_docs.py --strict` ✓ ·
`check_quality.py --check-only` ✓. #1995 ledger entry in `current-state.md`; no new owner
decisions (nothing for the router); no chat-only material — the root cause + fix live in
this card, the PR body, and the workflow file's own comments. Claim file deleted at close.
