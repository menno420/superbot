# 2026-06-23 — Final Review create-count guard + #1351 ledger drift fix

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Owner-directed (chat: "continue from where you left off" → the create-count confirmation summary
> teed up at the end of the #1357 wedge session). PR #1361 auto-merges on green (Q-0123).

## Arc

#1355/#1357 gave `/setup-describe` the power to **create** channels/roles from a description.
Creating resources is higher-impact and harder to undo than binding existing ones, so the apply
screen should call out *what will be made* before the operator commits — the polish flagged as
#1357's session idea (Q-0089). This session adds that guard.

Also: the SessionStart ledger check surfaced **#1351 (fishing trophy records) as real drift** — a
merge older than the reconciliation marker #1352 that the #1352 pass missed (not benign
newest-merge lag). Per Q-0166 ("fix drift you can SEE on sight"), fixed it in passing.

## Plan (this PR)

- `views/setup/final_review.py` — a `_created_resource_names()` helper (handles both staged shapes:
  `SetupOperation` create kinds → `resource_name`; `SetupRecommendation` `mode="create"` →
  `target_name`) and a distinct **"➕ N new resource(s) will be created"** field on the pre-apply
  embed, naming the resources. Bind-only plans are unchanged.
- `docs/current-state.md` — add #1351 to the fishing Recently-shipped bullet (drift fix; no new
  top-level entry, so the ratchet is unaffected).
- Tests in `test_final_review_caveat.py`.

**Contained:** rendering-only on the read path — no mutation/apply changes.

## Shipped (PR #1361)

- **`views/setup/final_review.py`** — `_CREATE_OP_KINDS` + `_created_resource_names()` (both staged
  shapes: `SetupOperation` create kinds → `resource_name`; `SetupRecommendation` `mode="create"` →
  `target_name`), and a distinct **"➕ N new resource(s) will be created"** field on the pre-apply
  embed naming the resources, with a "binding is reversible; a created resource must be deleted to
  undo" caveat. Bind-only plans render byte-identically.
- **`docs/current-state.md`** — #1351 added to the fishing Recently-shipped bullet (real drift fix,
  Q-0166).
- **Tests** — `test_final_review_caveat.py` +4: create op flagged · bind-only not flagged ·
  recommendation `mode="create"` flagged · `_created_resource_names` handles both shapes.

## Verification

- `python3.10 scripts/check_quality.py --full` → **All checks passed** (12054 passed, 48 skipped, 2 xfailed).
- `check_architecture --mode strict` → 0 errors (49 pre-existing warnings).
- Targeted: 73 final-review / draft / ai-review tests green. Ledger `--strict` → exit 0 (only benign
  newest-merge lag remains).

## Session enders

- **♻ Grooming (Q-0015):** executed this session's predecessor idea (the #1357 create-count guard)
  — idea → shipped in the next session (Q-0172). Also fixed #1351 ledger drift on sight (Q-0166).
- **💡 Session idea (Q-0089):** *Per-kind create breakdown in the guard* — the field currently shows
  a flat count + names; for a large plan, grouping by kind ("2 channels, 1 role, 1 category") would
  let an operator sanity-check the shape at a glance. Tiny rendering tweak on the same helper (it
  already has `op.kind`); dedup-checked `docs/ideas/`, not captured.
- **⟲ Previous-session review (Q-0102):** #1357 did well to ship the create path with full
  validation + tests AND name the exact next polish in its session idea, which made this session a
  clean 30-minute slice. *Workflow note:* the SessionStart ledger checker correctly separated benign
  newest-merge lag (#1355–#1358) from real older-than-marker drift (#1351) — that distinction (Q-0166)
  is working as designed and stopped me from either ignoring real drift or churning on benign lag.
- **📋 Doc audit (Q-0104):** no new commands/env-vars → no generated-artifact regen; ledger `--strict`
  green (real drift cleared); feature + follow-up captured here.
