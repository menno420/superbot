# Session — generated-artifact freshness umbrella (one drift reporter for every committed generated file)

> **Status:** `complete`
> **Branch:** `claude/magical-rubin-w937u6`
> **Date:** 2026-06-17

## What I'm about to do

Scheduled DISPATCH fire, **empty work order**. Oriented: the buildable-now ungated `ready`
queue is genuinely thin (BTD6 deterministic-floor lane essentially exhausted — #1024 shipped the
two named candidates; moderation-DM shipped #1023; dashboard write/manifest lanes are owner-paced;
image-mod #941 + security #929 are Hermes-review carve-outs; phase gate = FIX). All three committed
generated artifacts verified **currently fresh** this run, so there is no *drift to fix* — but the
gap the #1025 session flagged is real and durable: each artifact is guarded in isolation and nothing
prevents the next silent rot.

**Building the freshest captured idea** — the
[generated-artifact freshness umbrella](../docs/ideas/generated-artifact-freshness-umbrella-2026-06-17.md)
(Q-0089 from #1025), as **Q-0105 dev tooling** (read-only · stdlib · warn-only · disposable, with the
mandated provenance header; NOT hard-CI-wired — ask-first): `scripts/check_generated_artifacts_fresh.py`,
a registry-driven umbrella over the three committed-and-generated artifact families —
`dashboard/data/dashboard.json` (delegates to the existing `check_dashboard_data --drift`),
`docs/operations/env-vars.md` (env-var name identity set), and `docs/agent/generated/*.context.md`
(line identity, date line dropped). Reuses each artifact's own generator; compares structural
identity only (never the volatile churn — line numbers, timestamps), the #1025 lesson. Tests +
mark the idea built.

> Born-red gate (Q-0133): flip to `complete` as the deliberate final step.

## What shipped (PR #1027)

`scripts/check_generated_artifacts_fresh.py` — a registry-driven umbrella freshness reporter over the
three committed-and-generated artifact families, generalizing the #1025 single-artifact `--drift`
reporter so **no** committed generated file silently rots:

- `dashboard/data/dashboard.json` → **delegates** to the existing `check_dashboard_data.check_structural_drift`
  (reuse, not duplicate, per helper-policy).
- `docs/operations/env-vars.md` → env-var **name** identity set (the same regex applied to both fresh
  render and committed file — no extraction asymmetry; code `file:line` locations, which shift
  constantly, deliberately ignored).
- `docs/agent/generated/*.context.md` → per-pack content-line set with the volatile `> Generated:`
  date line dropped (the #1025 structural-vs-volatile lesson; rebuilt in-memory via `_render_pack`,
  never mutating the working tree).

**Warn-only by design** (always exit 0); `--strict` exits 1 for opt-in cadence use; `--list` prints
the registry. Built as **Q-0105 dev tooling** — read-only, stdlib, disposable, with the mandated
provenance/reliability header. **Not hard-CI-wired** (ask-first); the natural home for "keep the
generated artifacts fresh" is the docs-reconciliation cadence pass, where the dashboard regen was
just routed (#1025). 11 unit tests (incl. a load-bearing live guard asserting the committed artifacts
are *currently* fresh — they are). `check_quality --full` green (10483 passed) · arch 0 (only
pre-existing xp-view known warnings) · `check_docs` ✓.

**Phase-gate note:** the run opened in FIX phase (`check_phase_gate --require-invent` → exit 1). The
gate fences self-invented **bot features**; a read-only warn-only **dev-tooling** drift checker is
Q-0105 ("implement whatever tooling/check you judge will help, without asking") + Q-0129 ("self-
initiated action that improves the workflow is welcomed"), which override the gate for tooling. The
#1025 session captured this same idea as "not built, fix-phase" out of caution; this run made the
Q-0105 call to build it — the value is real and durable (catches the exact #1025 silent-drift class
for every committed generated file, including future ones).

## Codex review (PR #1027) — disposition

The Codex reviewer left four comments, **all describing the mid-flight born-red state**, not defects:
(P1) card is `in-progress` → gate holds red; (P2) the script isn't in the tree yet (first commit was
the card only); (P2) missing Q-0089/Q-0102 enders. All four are resolved by this close-out push (the
script + tests land, the enders are written, the card flips to `complete`). No code change was needed
in response — they were correct observations of work-in-progress.

## 💡 Session idea (Q-0089)

**A `reliability:` machine-readable tier on every Q-0105 "unverified/delete-if-unreliable" guard, and
a one-line `scripts/list_disposable_guards.py` that prints the inventory.** The repo now has a growing
family of Q-0105 convenience guards (`check_dashboard_data`, `check_branch_freshness`,
`check_generated_artifacts_fresh`, …), each carrying a prose "unverified — confirm across sessions,
delete if unreliable" header. But nothing *aggregates* them, so the "graduate to verified, or delete
if it proved unreliable" half of Q-0105 never actually fires — a guard that's been quietly wrong for
five sessions has no surfacing mechanism; it just accretes. A tiny stdlib lister that greps for the
provenance header (date-added + tier) and prints `guard · added · tier · verdict-needed?` would give
the reconciliation pass a standing "review the disposable guards" checklist — closing the Q-0105 loop
the same way the freshness umbrella closes the generated-artifact loop. (Dedup-checked `docs/ideas/`:
the closest is the freshness umbrella itself, which is about *artifacts*, not *guards* — distinct.)
Worth having because Q-0105's kill-switch is only real if something reminds an agent to pull it.

## ⟲ Previous-session review (Q-0102)

The previous run (**#1025**, dashboard.json structural-drift reporter + regen) did a genuinely good
thing: it didn't just regenerate the stale `dashboard.json`, it built the *structural-vs-volatile*
drift reporter that explains **why** it was stale and prevents recurrence — and it correctly captured
the generalization (this umbrella) as an idea rather than scope-creeping it into the same PR. What it
**could have done better**: it left the umbrella captured-not-built citing "fix-phase," but a read-only
warn-only dev-tooling checker is exactly the Q-0105 carve-out the phase gate does *not* cover — so the
generalization sat one run longer than it needed to. **System improvement this surfaces:** the phase
gate's output should say *what it does and does not fence* (it fences self-invented **bot features**,
not Q-0105 dev tooling) — right now an agent reads "Phase: FIX" and over-applies it to tooling. A
one-line clarification in `check_phase_gate.py`'s banner ("this gate fences self-invented bot features
only; Q-0105 dev tooling/checks are free-rein") would have saved this run the re-derivation. Captured
as the seed of the `reliability:`-tier idea above; the banner tweak is a clean next-run docs/tooling
fix.

## Q-0104 doc audit

`check_current_state_ledger --strict` green · `check_docs --strict` green · idea file + `ideas/README.md`
index both flipped to `IMPLEMENTED #1027` · current-state ▶ handoff sharpened. No owner decision was
made this run (the Q-0105/promotion-gate calls are agent-discretion under standing directives, not new
owner policy), so nothing to route to the question router. BUG-0009 (slice 3, data-gated) and BUG-0011
(Hermes gateway crash-loop, VPS-infra) stay OPEN — neither is fixable in this repo this run.
