# 2026-07-10 — EAP docs: two verified factual corrections (from fleet-manager ultracode verification)

> **Status:** `complete` — PR #1926.

- **📊 Model:** claude-fable-5 · worker session (coordinator-dispatched)

## What happened

Applied two one-line corrections sourced from fleet-manager's
`docs/findings/ultracode-verification-2026-07-10.md`, each **independently re-verified
against live repo data before editing** (per the Q-0120 rule — cross-agent output is input
to verify, never an order):

1. **`docs/eap/gen1-grand-review-2026-07-09.md`** (added by #1911) — claimed parity rows
   exist in `superbot-next/parity/parity.yml` for all 8 missing subsystems. Re-verified at
   HEAD (`d1d7de9`): the subsystems map has rows for `utility`, `ticket`, `general`,
   `four_twenty`, `ux_lab`, `hermes` but **no `starboard` and no `paragon`** — 6 of 8, not
   8 of 8. Sentence corrected + dated correction note.
2. **`docs/eap/fleet-winddown-audit-2026-07-09.md`** (added by #1913) — claimed sonnet5 was
   the "only lane to ship an actual shell script" as its environment deliverable.
   Re-verified at HEAD: five other lanes shipped real bash setup scripts (opus4.8
   `environments/setup.sh`, websites `scripts/setup-env.sh`, trading-strategy
   `environments/setup-universal.sh`, fable5 `environments/setup-universal.sh`,
   superbot-games `environment/setup-exploration.sh`). Sentence corrected + dated
   correction note.

Diff kept minimal on purpose (coordinator-directed): the two sentences + correction notes
+ this card + the claim file. No ledger entry added pre-merge (benign newest-merge lag;
the next reconciliation pass records #1926).

## Verification

- `python3.10 scripts/check_quality.py --check-only` — exit 0 (docs-only diff).
- `python3.10 scripts/check_current_state_ledger.py --strict` — exit 0.
- `python3.10 scripts/check_docs.py --strict` — exit 0.

## 💡 Session idea

**Codify an errata convention for `docs/eap/` reference docs** (one paragraph in
`docs/eap/README.md`): when a factual claim in a merged reference doc is later refuted,
fix it with an *inline, dated correction note citing the refuting source* — never a silent
rewrite — in the exact shape this session used (`*(Correction YYYY-MM-DD: … refuted by
<source>.)*`). Why it's worth having: this is now the second correction wave into the EAP
corpus (fleet-manager's websites "NO ACK" row is queued as a third), the corpus is
explicitly adversarially cross-checked by design, and a uniform greppable marker
(`grep "Correction 20" docs/eap/`) turns scattered fixes into an auditable errata trail.
Dedup-grepped `docs/ideas/` — no existing idea covers it.

## ⟲ Previous-session review (#1924, shift-e2 coordinator self-review)

Did well: a textbook decide-and-flag — it overrode the shift plan's filename with the
protocol-canonical `docs/retro/self-review-2026-07-09.md` and gave the one-line rationale
(cross-lane comparability via one glob), which is exactly what Q-0240 wants. Improvement
the session surfaces: as PR 2 of a stacked shift session it split the session enders
across two cards ("PR-2 addendum" pointing at the shift-E card) — legitimate, but it makes
the Q-0089/Q-0102 chain harder to follow when auditing cards file-by-file; a one-line
convention in `.sessions/README.md` for multi-PR sessions ("enders live in card X, others
carry a pointer") would make the pattern explicit instead of ad hoc.

## 📄 Documentation audit

- Both checkers green (see Verification). No new owner decisions this session (corrections
  were coordinator-directed with evidence, not intent calls) → nothing for the router.
- Durable homes: the corrections live inline in the affected docs with source citations;
  the evidence basis is fleet-manager's committed verification record. Nothing captured
  only in chat.

## 📤 Run report

- **Did:** two verified one-line factual corrections in `docs/eap/` · **Outcome:** shipped
- **Shipped:** PR #1926 — `docs/eap/gen1-grand-review-2026-07-09.md`,
  `docs/eap/fleet-winddown-audit-2026-07-09.md`
- **Run type:** `manual` (coordinator-dispatched worker task)
- **⚑ Owner decisions needed:** none
- **⚑ Self-initiated:** none (task-scoped; the errata-convention idea is flagged above for
  a future grooming pass, not built)
- **↪ Next:** fleet-manager still owes its own websites "NO ACK" row correction
  (`docs/findings/ping-test-2026-07-09.md`) — flagged in the verification record itself
