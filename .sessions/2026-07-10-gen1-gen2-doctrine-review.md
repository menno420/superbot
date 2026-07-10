# 2026-07-10 — gen1-gen2-doctrine-review

> **Status:** `complete` — independent doctrine review shipped as `docs/eap/gen1-gen2-doctrine-review-2026-07-10.md`; every quoted line verified against both repos at HEAD.

**Intent:** Owner-directed independent external review — compare the new
`fleet-manager` gen-2 coordination doctrine against superbot's original
battle-tested doctrine across four axes (contradictions, regressions,
duplication, portability), with a file+quoted-line for every claim and UNVERIFIED
marks where a claim couldn't be checked. `menno420/fleet-manager` was added to
session scope and cloned to `/workspace/fleet-manager` (HEAD `8e08cd0`); superbot
read at `77b76de`.

## What shipped
- `docs/eap/gen1-gen2-doctrine-review-2026-07-10.md` — the review: plain-language
  executive summary, a verdict table, findings by question with severity +
  evidence, a "rejected criticisms" record, a bonus internal-consistency section,
  and 5 tagged recommendations ([backport to superbot] / [fix in gen-2] /
  [accept divergence]). Badge `audit`.
- `docs/current-state.md` — linked the review as a follow-on to the #1887/#1889/
  #1890 fleet-review entry (reachability, no new Recently-shipped bullet → ratchet
  untouched).

## Method (why the conclusions are trustworthy)
- Orchestrated 30 passes: 4 independent per-question analyses → adversarial
  `grep`-verification of **every** quoted line against the file at HEAD → a
  completeness/overreach critic. Two plausible criticisms were **rejected** on
  verification (superbot's auto-merge is "silently failing" — false; a
  cite-don't-copy inconsistency built on a **fabricated** superbot quote), and
  three severities were downgraded when the adversarial pass showed overreach.
- Caught the framing trap up front: gen-2 did **not** drop session cards /
  friction→guard / reconciliation — all are present and several CI-enforced
  (`substrate-gate.yml`, `substrate.config.json`). The honest regressions are
  narrower (hollow ledger gate, missing doc-audit ender).

**Verified against ground truth:** `check_docs --strict` clean after the
reachability link; `check_quality.py --check-only` green (docs-only change, no
`disbot/` touched); `check_session_gate` satisfied (card complete + telemetry row
appended).

📊 **Model:** opus-4.8 · effort high · task_class docs-only (review/analysis).

💡 **Session idea:** *A `check_doctrine_parity.py` cross-repo guard.* This review
found the program's real drift risk is **duplicated rule/format bodies across
repos** (status/inbox format in ≥3 homes; the collaboration kernel in 4+; two ID
registers for one ruling). superbot already owns the tooling philosophy (custom
AST checkers). A small checker that hashes the canonical block (e.g. the
`control/` status/inbox format, or a cited PL-body) and flags when a declared
"local copy" drifts from its canonical source would turn "cite-don't-copy" from
an exhortation into an enforced guard (Q-0194 friction→guard) — and is exactly
the format-parity check the review recommends for the fleet.

⟲ **Previous-session review** (`2026-07-09-telemetry-gate-guard`): Strong session —
it did the right thing turning an *observed* leak (3 telemetry rows vs ≥4 carded
sessions) into an enforcing merge-gate rather than a note, the textbook Q-0194
"enforce, don't exhort" move, with both directions live-tested and a self-
consistent row for its own PR. One improvement it points to for the *system*:
that guard proves superbot enforces telemetry/session discipline via
`check_session_gate`, but the parallel **ledger-completeness** guard
(`check_current_state_ledger`) is only wired into `/session-close`, not the merge
gate — so a merged PR absent from the living ledger isn't hard-blocked the way a
missing telemetry row now is. Promoting ledger-parity to the same born-red gate
would close the asymmetry (and is the mirror of this review's #1 forward-port
recommendation for gen-2).
