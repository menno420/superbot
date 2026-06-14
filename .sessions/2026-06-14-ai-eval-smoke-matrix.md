# Session: P1-1 — versioned AI eval/smoke matrix (offline half)

> **Status:** `in-progress`

**Branch:** `claude/wizardly-edison-xw34kb` · **PR:** (opening) · **Date:** 2026-06-14 · **Type:** AI hardening / tests (P1-1, band-#870 queue slot 2)

## What I'm about to do (born-red declaration)
Build the **offline/deterministic half** of the versioned AI eval/smoke matrix — the standing #1
priority (P1-1), `ready` per the [band-#870 decade queue](../docs/planning/reconciliation-pass-2026-06-14-band870.md) §4 slot 2.

The live golden set (`tests/evals/cases.py`) is paid/creds-only; CI only exercises the harness
machinery, never the AI path's **deterministic contract**. This session adds the missing
versioned, CI-gated artifact covering **gates · fallback · tool-dispatch · audit-visibility ·
redaction · safety** through the real gateway pipeline (scripted providers, no API), producing one
scorecard record. Plus: version the whole matrix and add the #855 Layer-A live regression probe.

**Out of scope (correctly gated):** absence-claim guard **Layer B** stays design-for-review (the
design doc's own definition-of-done) + the live eval battery needs prod creds.

## Coordination
Concurrent docs-only session #877 (sectors/roadmap). This PR is **bot tests + scripts** only —
no overlap on `disbot/`/roadmap. I touch `docs/current-state.md` in my own lane bullet +
Recently-shipped only (UNION-safe) and append one `active-work.md` claim.

_(filled in at session close: shipped / verified / idea / review / doc audit)_
