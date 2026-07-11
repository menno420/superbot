# 2026-07-11 — Fix codex-final-review workflow YAML (broken since #1105)

> **Status:** `in-progress`

📊 Model: Fable 5 · coordinator-directed lane session (CI fix) · day

## What this session is about to do

Fix the born-broken `.github/workflows/codex-final-review.yml`: it has been invalid YAML
since its creating commit `bfe99084` (PR #1105, 2026-06-19) — the multi-line `--body` string
in the last step de-indents out of the `run: |` block scalar, so every trigger since has been
an instant "Invalid workflow file" failure (~2,808 runs, zero successes).
