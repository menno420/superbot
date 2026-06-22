# 2026-06-22 — migration-number collision guard (kill the renumber treadmill)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch ("Continue from where you left off"; grooming-executes a logged idea).
> PR #1322 → auto-merges on green (Q-0123).

## Arc

Four PRs already merged this session (#1305 React foundation, #1308 contract guard, #1317 ledger/CI
hygiene, #1320 tool-pin CI guard). Product lanes are gated (PR 2 cutover needs attended browser
verification; Project Moon ingestion is network/IP-sensitive; bug-book rootfix backlog = BUG-0009
data-gated + BUG-0019 owner design-fork) and the recon is the separate routine's job (Q-0124). So
this turn takes the **sanctioned grooming pick** (Q-0015): execute a small/safe/decided-lane idea —
`docs/ideas/migration-number-collision-guard-2026-06-22.md`, Option 1.

**Real recurring bug** (not busywork): migration files are `NNN_name.sql` numbered off a single
shared append point, so concurrent fleet PRs pick the *same* next number and collide against `main`.
#1279's migration was renumbered **four times in one afternoon** (085→086→088→089). CI tests the
merge result so it goes red, but a branch-only local `check_quality.py --full` passes (never merges
with main) — the author gets green-local / red-CI with no obvious cause.

This PR (Option 1 — the cheapest, highest-value):
1. **`scripts/check_migration_collision.py`** (stdlib, read-only): compare the branch's *new*
   migration numbers (working tree) against `origin/main`; on a collision print the next free number
   + the exact `git mv` to renumber, **before** the push/CI round-trip. Covers `disbot/migrations/`
   + `botsite/migrations/`. Pure `analyze()` core + thin git I/O. Disposable-guard header (Q-0105).
2. **Tests** — the pure analyzer (collision detect, next-free suggestion avoiding taken numbers,
   no-collision clean, multi-collision cascade, non-migration files ignored).
3. **Idea bookkeeping** — mark Option 1 done in the idea file (Options 2/3 remain).
4. **Stale-claim GC** — delete my merged-branch claims (`s56i3y-3`, `s56i3y-4`).

**Not wired into the Stop hook** (that's a hook edit, Q-0106 — owner-only). The script is standalone +
documented; a follow-up can wire it into `/pre-pr` (a skill, editable) or the hook (owner consent).

## Shipped (PR #1322)

- **`scripts/check_migration_collision.py`** (stdlib, read-only): compares the working tree's
  migration numbers against `origin/main` (via `git ls-tree`, no fetch/no writes) for both
  `disbot/migrations/` + `botsite/migrations/`. On a collision it prints the offending file, the
  number already on main, the next free number, and the exact `git mv` to renumber. Pure
  `analyze(base, head)` core + thin git I/O; gracefully exits 0 if `origin/main` is absent (says to
  fetch). Disposable-guard header (Q-0105). Runs clean on the current repo.
- **Tests** (`tests/unit/scripts/test_check_migration_collision.py`, 7): `parse_number`; no-collision
  (fresh number / no additions); the #1279 reuse case; multi-collision distinct suggestions; a fresh
  high number + a collision (suggestion skips the taken 090 → 091); the `git mv` zero-padded swap.
  (Loader registers the module in `sys.modules` before exec — `@dataclass` needs it, unlike the
  no-dataclass tool-pins test.)
- **Idea bookkeeping** — `migration-number-collision-guard-2026-06-22.md` status → Option 1 SHIPPED
  (Options 2/3 remain).
- **Stale-claim GC** — removed my merged `s56i3y-3` + `s56i3y-4` claims.
- **Verification:** new tests 7/7 ✓ · `check_quality --check-only` ✓ · guard runs clean on the
  real repo (exit 0). (mypy is `disbot/`-scoped in CI; `scripts/` isn't type-gated.)

## Session enders

- **♻ Grooming (Q-0015):** this turn *was* the grooming task — executed a small/safe/decided-lane
  `docs/ideas/` entry (migration-collision guard Option 1) now that the main lanes are gated, exactly
  the "capacity remains → move one idea down its lifecycle" path. Idea file updated to reflect it.
- **💡 Session idea (Q-0089):** *Wire the migration guard into `/pre-pr` (a skill, not a hook).* The
  guard only helps if it's *run*; the idea doc wanted the Stop hook, but a hook edit is owner-only
  (Q-0106). `/pre-pr` is a skill (editable) and is exactly the "before you push" moment the guard
  targets — adding `python3.10 scripts/check_migration_collision.py` as an advisory `/pre-pr` step
  would give it an automatic surface without touching a hook. Small, safe; logged for a follow-up.
- **⟲ Previous-session review:** #1320 (this turn's predecessor) was a clean tooling slice, but it —
  and this whole session's tail (4 of 5 PRs were infra/guards) — surfaces a real pattern worth naming:
  **when the product lanes are all gated, the routine drifts into building guard after guard.** That's
  legitimately first-class work (CLAUDE.md), but **system note:** the dispatch routine has no signal
  that distinguishes "genuinely out of ungated product work" from "conservatively judging product work
  gated." A `current-state` field that lists the *ungated* startable product slices (vs the gated
  ones) — or the `dispatch_menu --json` resolver surfacing "0 ungated product lanes" explicitly — would
  let a run *confirm* the gate rather than infer it, and would tell the owner "the fleet is
  infra-bound, it needs you to unblock product." Captured as an observation, not built (it's the
  dispatch-resolution lane, Q-0143/#885 territory).
- **🧾 Doc audit (Q-0104):** `check_docs --strict` ✓ (run at close); idea file updated; no
  current-state/sector change needed (a dev guard, not a product feature); ledger auto-updates for
  #1322 on merge. Nothing left only in chat.

## ⚑ Self-initiated: yes (Q-0172) — grooming-executed a logged idea (migration-collision guard Option 1)
   with no dispatch/owner ask, the sanctioned Q-0015 path on an empty "continue" fire with gated product
   lanes. Stdlib, read-only, additive, tested → self-merged on green. Reversible (delete the script).

## 📤 Run report

- **Did:** grooming-executed a logged idea — `scripts/check_migration_collision.py`, a pre-push guard for the duplicate-migration-number class that renumbered #1279's migration four times (concurrent fleet PRs off the shared append point). · **Outcome:** shipped
- **Shipped:** #1322 — the guard + 7 tests + idea-file bookkeeping + stale-claim GC. Stdlib, read-only.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none` (optional follow-up: wire the guard into `/pre-pr` so it runs automatically before pushes).
- **⚑ Self-initiated:** **yes** — sanctioned Q-0015 grooming (executed a small/safe/decided-lane idea) on an empty "continue" fire with gated product lanes; additive read-only guard + tests → self-merged on green.
- **↪ Next:** product lanes remain the priority once attended/un-gated. **botsite React-SPA migration PR 2** (the live `/` cutover) is the top S1 item but needs a **manual browser click-through** → best attended/owner-previewed; its data side is now de-risked by #1305/#1308/#1317/#1320. Other lanes still gated: Project Moon runtime PR 1 (ingestion — network + IP/licensing → ask-first), bug-book BUG-0009 (data-gated) + BUG-0019 (owner design-fork). **Note for the owner:** this session shipped 5 PRs but 4 were infra/guards because the product roadmap is owner/attended-gated — the fleet is currently infra-bound and would benefit from you unblocking PR 2 (a browser look) or a product decision.
