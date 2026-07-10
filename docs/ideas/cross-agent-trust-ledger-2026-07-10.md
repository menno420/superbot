# Cross-agent trust ledger — per-model scores from repeatable eval suites

> **Status:** `ideas`
> **Subsystem:** none
> **Captured:** 2026-07-10 (session ender, Q-0089, GPT-5.6 Sol eval session)
> **Outcome:** IMPLEMENTED same day — `docs/owner/cross-agent-trust-ledger.md`
> seeded with the scored Sol/Codex run (eval doc §8) in the scoring session.

## The idea

`docs/owner/gpt-5-6-sol-codex-eval-2026-07-10.md` ships a repeatable prompt suite
that scores an external model on two axes (capability, trust) against ground truth
in this repo. Generalize that into a standing **trust ledger**: one small table —
model · date tested · P1–P6 scores · allowed lanes (reviewer / fenced sweep /
none) — updated whenever a new model version lands or an existing one misbehaves.

## Why it's worth having

Q-0120 already says cross-agent output is input-to-verify, never an order — but
*how much* verification each model's output needs is currently tribal knowledge
that evaporates between sessions. A ledger makes routing decisions ("send the
sweep to Codex, keep architecture with Claude") data-driven, cheap to re-derive,
and self-updating: re-run the same suite on each model release and diff the scores.
The Sol launch is the motivating case — record eval-gaming rates mean model-version
upgrades can silently *lower* trustworthiness while raising capability, which a
static mental model never catches.

## Shape (when groomed)

- `docs/owner/cross-agent-trust-ledger.md` — the table + one line per entry
  linking the session/log where the suite was run.
- The eval suite doc becomes the shared instrument; per-model result logs live in
  `.sessions/` as usual.
