# Session — 2026-06-25 · setup-wizard PR 3a — retire dead/legacy sections

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.

## What this run did

Empty-fire dispatch → advanced the S1 ▶ next slice: **setup-wizard PR 3** (the prior session's named
handoff). PR 3 has two halves; I shipped the contained, offline-verifiable half as **PR 3a** (PR #1451)
and handed off the rest as PR 3b.

**PR 3a — retire the dead/legacy sections from the (now-Advanced) wizard.** Per the owner-greenlit plan
§3/§7 disposition, the old section-list wizard (now `!setupadvanced`) still showed read-only / metadata /
announcement / link-only steps whose function moved into the Essential Setup spine (step 0 + "Check my
setup", PR 1/2). The wizard hub is registry-driven, so retiring a section = removing its
`REGISTRY.register(...)`:

- **Deleted** (7 fully orphaned modules, no non-test importer): `purpose`, `identity`, `btd6`,
  `ai_setup`, `readiness`, `diagnostics` (the section view — the `setup_diagnostics` *service* stays),
  `suggestions`. Their per-section test files deleted too.
- **Unregistered, module kept**: `server_scan` — `channels` imports `get_cached_snapshot`, so the module
  survives as a thin snapshot-cache seam (button + `run` removed). `channels` already degrades gracefully
  to a `None` snapshot, so its UX is unchanged.
- **Demoted** `cleanup` → advanced-only depth (`cog_routing` already was).
- Fixed a stale comment in `moderation.py` that pointed at the deleted `identity.py` (drift-on-sight).

**Tests:** `test_section_registration` rewritten to pin the surviving production set + a
`_RETIRED_SLUGS`-not-registered assertion + a cleanup-is-advanced-only assertion; the three hub auth-gate
tests retargeted from the retired `readiness` button to the surviving `final_review` button (the gate is
uniform); the readiness/suggestions section-specific hub tests deleted; `test_btd6_setup_section_registered`
→ `test_btd6_setup_section_retired`; jargon ratchet lowered 154 → 133 with the deleted files pruned from
`_BASELINE_FILES`.

## Verification
- `check_quality.py --full` GREEN (12451 passed after the btd6-test fix) · `check_architecture --mode
  strict` exit 0 · `check_docs --strict` ✓ · `check_current_state_ledger --strict` exit 0.
- `setup_wizard_sim.py` still **PASS** on all four owner goals.

## Deferred → PR 3b (needs live-bot verification)
The Q-E Advanced draft→Final-Review editor rework ("currently most of it does not do anything") + deleting
the now-dead service code PR 3a leaves behind (e.g. once `channels` drops its snapshot lookup, the
`server_scan` cache seam can go). Heavier; wants a running bot to confirm the editor's live behaviour
before stripping actions.

## 💡 Session idea (Q-0089)
*A "live setup section" CI guard.* PR 3a retired dead sections by hand-judgment against the plan's §3
rubric ("does this step complete a real action?"). That rubric could be a small disposable check —
`check_setup_sections_live.py` — that flags a *registered* section whose `run` does no real work (heuristic:
empty `op_kinds` AND no audited-write / mutation call in its module AND not the `final_review` dispatcher),
so the next dead-section accretion is caught in CI instead of waiting for an audit. It turns the one-off
disposition judgment I just made into a standing guard. (Genuinely useful; tied directly to today's work —
not filler.)

## ⟲ Previous-session review (Q-0102)
The previous run (2026-06-25 stale-claim-detector) did its best work in the *pivot*: it set out to build a
stale-claim detector, grepped first, found the tool already existed, and correctly re-scoped to a routing
finding (Q-0206) instead of rebuilding it — exactly the "grep before you build" discipline Q-0200 pushes,
applied to *review notes* too. What it could have done better: both its slices started as "build" tasks and
ended shipping zero runtime code (one because the tool existed, one because badges needed a running bot) —
defensible individually, but a dispatch run that *can* ship runtime work ideally confirms a build slice is
real before claiming it. **System improvement it surfaces:** the dispatch handoff would be sharper if the
▶ Next line tagged each startable with a *verifiability* hint (offline-buildable vs needs-live-bot) — this
run's S1 list mixes both (PR 3b needs a bot; PR 3a didn't), and I only learned that by reading the plan. A
`needs-live-bot` / `offline` tag on each ▶ startable would let an autonomous run pick the offline one
without spelunking. (I've applied that informally in the PR 3b handoff below — worth making a convention.)

## Doc audit (Q-0104)
Ledger in sync (the #1442–#1450 merges newer than the #1441 marker are benign newest-merge lag, Q-0166).
Setup-wizard plan (§ build-progress banner + §7) and S1 sector ▶ Next de-staled to PR 3a-shipped /
PR 3b-remaining. No owner decision this run (PR 3a executes the already-greenlit plan). Claim file deleted
at close.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** **PR #1451** — setup-wizard PR 3a (retire 7 dead sections + unregister `server_scan`
  button + demote `cleanup`); plan + S1 sector de-staled.
- **⚑ Self-initiated:** none — this is the explicit S1 ▶-next plan slice (owner-greenlit setup-wizard plan
  §7 PR 3), dispatched via an empty-fire advance.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (registry-only change; merge auto-deploys; no data/seed step).
- **Bug-book:** none fixed (BUG-0009 newest-towers data-gated, BUG-0011 needs VPS repro, BUG-0019 #1
  awaits an owner behavior decision — all unchanged); none newly opened.
- **Handoff (▶ Next):** S1 = setup-wizard **PR 3b** — rework the Advanced draft→Final-Review editor
  (Q-E) + delete now-dead service code (`channels` snapshot lookup → drop the `server_scan` seam).
  **`needs-live-bot`** (verify the editor's live behaviour before stripping actions) — heavier, own
  session. Other S1 startables unchanged: Project Moon PR 1, botsite React PR 2, the card-engine H3
  incremental `help_nav_card` adoption (all `offline`).
