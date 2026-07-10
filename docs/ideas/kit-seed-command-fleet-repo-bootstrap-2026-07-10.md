# Kit `seed` command — one-shot fleet-repo bootstrap (adopt + engage + lane layer)

> **Status:** `ideas` — state: captured; origin: the round-3 dispatch part-3 session
> (2026-07-10), which hand-seeded TWO fleet repos (`idea-engine`, `product-forge`) with
> the identical ~10-step sequence. Subsystem: agent-ecosystem / substrate-kit.

**The idea.** The seeding sequence is now proven and completely mechanical: copy
`dist/bootstrap.py` → `adopt` → answer the ~13 interview slots → `render --live` →
`mode guided` → wire the staged gate into `.github/workflows/` → plant the lane layer
(role README, CONVENTIONS.md, claims/, review-queue.md, PLATFORM-LIMITS.md, retro
questions, control/outbox where the role needs one) → seed card + heartbeat +
`session-close` → `check --strict` green → push. Two hand-runs hit the same three
gotchas (empty-clone refspec unset; retro-questions badge/reachability findings;
strict-check gate must directly precede the push). A kit-side
`bootstrap.py seed --profile <lane|coordinator|lab>` (or a checklist-driving script)
would collapse this to one command + a slot-answers file, making every future fleet-repo
birth (sim-lab is next; the 3-repo games program right behind it) a 5-minute
deterministic step instead of a 40-minute hand-run.

**Why it's worth having.** Repo births are now a recurring fleet operation (13 repos and
growing; Q-0259 adds three more). Every hand-seed re-derives the same order and re-hits
the same gotchas; the kit already owns every piece (adopt, render, check, session-close)
— only the orchestration and the lane-layer templates are missing, and the lane layer is
exactly the render/engage half the EAP fleet review flagged as stranding in fresh
adoptions (#1890 headline finding — this is its fix's natural home).

**Route.** Kit-owned feature → the substrate-kit lane's backlog (the Idea Engine's
`ideas/substrate-kit/` section harvests this file; the probe should weigh profile shapes
and whether slot-answers ship as a committed file the seed reads).
