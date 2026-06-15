# Respec numbers — mining Slice E (respec polish)

> **Status:** `reference` — the pinned coin numbers for the skill-tree respec lane
> (full + single-branch). Tunable; change them here **and** in
> `services/skill_service.py` + the test in the same commit (the
> `gear-set-numbers-2026-06-15.md` convention). Source wins.

The skill tree (Slice D, #891) shipped a **full respec** only. Slice E adds the
UX confirm + a cheaper **single-branch** respec. Both are level-scaled coin sinks
through the audited economy lane (`economy_service.debit_in_txn` inside the
respec transaction).

| Action | Base | Per-level | Cost at L0 | Cost at L20 | Reason code |
|---|---|---|---|---|---|
| Full respec (`respec`) | `RESPEC_BASE_COST` = 200 | `RESPEC_COST_PER_LEVEL` = 50 | 200 | 1200 | `mining:skill_respec` |
| One branch (`respec_branch`) | `RESPEC_BRANCH_BASE_COST` = 75 | `RESPEC_BRANCH_COST_PER_LEVEL` = 25 | 75 | 575 | `mining:skill_respec_branch` |

**Invariant:** a single-branch respec always costs **less** than a full respec at
the same level (you only re-spend one branch). Pinned by
`test_respec_branch_cost_is_cheaper_than_full_and_scales`.

The confirm step (`build_respec_confirm_embed` + `MiningRespecView`) charges
nothing until the player picks an option — the Respec button no longer respecs
instantly.
