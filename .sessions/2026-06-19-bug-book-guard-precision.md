# 2026-06-19 — Harden the bug-book root-fix guard (#1144 Codex-review follow-up)

> **Status:** `complete`

## Arc

PR #1144 (the deferred-root-fix backlog guard) auto-merged on green before its Codex review
landed. The review raised three valid precision points about the classifier — worth fixing now that
the tool is on `main` (warn-only, so low-stakes, but the false-positive risk would bite `--strict`).

## What the review found (and the fix)

The classifier was fed the **whole header tail (title included)** and matched **loose substrings**:

1. **Immediate + "root" prose** — `"IMMEDIATE" in upper and "ROOT" not in upper` suppressed a genuine
   `FIXED (immediate)` entry whose deferral text said "root cause deferred" (the word "root" tripped it).
2. **Bare `PARTIALLY`** — matched a *title* like "counting partially ignores …", false-positiving an
   honestly-`FIXED`/`OPEN` entry (contradicting the documented OPEN exclusion; would redden `--strict`).
3. **Terminal-first ordering** — hardening to classify the terminal `(root)` marker before treating a
   `RECOMMENDED`/recommendation mention as deferred work.

**Fix (one root cause — scope + precision):**
- New `_header_status_label()` extracts only the **status label** (segment after the *last* em-dash) —
  the title is never scanned for status signals.
- `_classify` now matches **precise phrases / parenthesized markers**: `(root)` short-circuits first;
  `PARTIALLY FIXED` (phrase); `RECOMMENDED` (word — "recommendation" no longer matches); `(immediate)`
  (parenthesized label) keyed on the `(root)` *marker* absence, not any "root".

## Verification

- 4 new tests cover all three review cases (title-"partially" not flagged; immediate-with-"root cause"
  prose still flagged; terminal-FIXED-with-"recommendation" not flagged; belt-and-braces title with
  both "root" + "partially"). 13 tests pass.
- Live run on current `main` correctly reports only **BUG-0009** (BUG-0018 now `FIXED (root)`).
- `check_quality --check-only` green; full mirror run before push.

## 📤 Run report

- **Run type:** routine · dispatch
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** YES — hardening follow-up to the self-initiated #1144 guard, prompted by its
  Codex review (no dispatch/owner ask). Reversible (warn-only disposable tool).
