# 2026-07-02 — Memory retention & deletion policy (design session)

> **Status:** `in-progress`

**About to do:** Owner-directed design brainstorm (not a build): rethink how the
AI-memory/docs system retains vs. sheds content. Ground the current
archive-everything conventions against the repo (plan-index never-delete rule,
orientation budgets, check_docs ratchets, Q-0210 router archive, the active
orientation-cost-reduction plan), converge on a retention/deletion policy +
hardcoded limits, and design (prototype if converged) a retention simulator
that finds the limit numbers empirically. Deliverables: a `docs/planning/`
plan extending orientation-cost-reduction-plan-2026-06-30, a
`tools/sim/retention_sim.py` prototype, and the trade-off analysis — ready to
hand to an implementation session. No runtime (`disbot/`) code; no actual
deletions this session.
