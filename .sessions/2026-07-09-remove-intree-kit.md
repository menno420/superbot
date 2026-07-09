# 2026-07-09 — Remove the in-tree substrate-kit copy (named follow-up chore)

> **Status:** `in-progress`

## What I'm about to do

Execute the follow-up chore named in the kit-lab founding plan §4.2
(substrate-kit `docs/planning/kit-lab-founding-plan-2026-07-07.md`: "the
in-tree `substrate-kit/` source dir deletion stays a follow-up superbot
chore"): delete `substrate-kit/` and `tests/unit/substrate_kit/` — the kit
graduated to menno420/substrate-kit (v1.0.0 released; KL-2 merged there),
superbot's pin is `substrate.config.json` (#1879) — after verifying nothing
in superbot imports or runs from the in-tree copy, and repoint the living-doc
references at the graduated repo.
