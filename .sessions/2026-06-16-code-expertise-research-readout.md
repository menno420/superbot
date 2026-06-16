# Session — Claude Code expertise research: workflow grounding

> **Status:** `complete`

## Origin

Owner asked me to read Anthropic's "Agentic coding and persistent returns to expertise"
research (anthropic.com/research/claude-code-expertise) and report whether anything in it
is usable in our workflow. Readout delivered in chat; the report **confirms** our model
rather than exposing a gap, so the owner approved two contained doc follow-ups.

## What shipped (this PR — docs only)

1. **`docs/collaboration-model.md`** § "Why this system exists" — added an *External
   grounding* paragraph citing the ~400K-session study for the two premises it confirms:
   the **70/30 plan-vs-execute split** ("people decide *what*, agents decide *how*" ≈ our
   Q-0014) and **domain expertise beats coding background** (non-tech pros within ~4 pts of
   engineers) — the empirical case for the docs/orientation system that turns the
   maintainer's domain knowledge into precise specification.
2. **`docs/ideas/success-metric-alignment-with-verified-success-2026-06-16.md`** (+ README
   index) — the report's *verified success* metric (hard signals: tests/commits/confirm)
   matches our CI-green + auto-merge + born-red gate; small audit idea on naming the
   CI-only vs. human-confirm session lanes.

## Verification

- `python3.10 scripts/check_docs.py --strict` → green (312 docs, all reachable).
- Docs-only; no `.py` touched, so no mypy/pytest delta.

## 💡 Session idea (Q-0089)

Captured as the idea file above — align our session success proxy with the research's
"verified success" definition; name which session classes need explicit owner confirmation
before auto-merge vs. CI-only.

## ⟲ Previous-session review (Q-0102)

Previous session (`2026-06-16-multiuser-control-panel-design.md`) was a clean docs-only
design capture — strong on *auditing the existing seam before proposing new work* (it
confirmed per-user + per-guild config already exist rather than assuming a build was
needed). What it could improve: it left two build questions ("cog-vs-command enable/disable";
`/commands` management go-ahead) explicitly open with no router Q-block to track them, so
they live only in that log's prose — exactly the drift class our router exists to prevent.
**System improvement it surfaces:** when a session defers a *decision* (not just an idea),
the close-out should route it to a DISCUSS-lane Q-block, not a session-log sentence — a
deferred decision in prose is invisible to the next session's orientation. Worth a one-line
addition to the Q-0104 audit checklist: "any decision deferred this session → is it a
router Q-block, not just log prose?"

## Documentation audit (Q-0104)

- New owner-approved doc changes have durable homes (collaboration-model.md + ideas/ +
  README index). `check_docs --strict` green.
- No new owner *decision* to record in the router (this was a "go ahead if useful"
  approval of contained docs work, not a policy decision).
- Ledger: SessionStart flagged 4 merged PRs not yet in current-state — that is the
  routines' automated reconciliation scope (Q-0124), not this manual session's task; left
  for the reconcile trigger.
