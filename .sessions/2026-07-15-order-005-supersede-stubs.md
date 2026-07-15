# 2026-07-15 — ORDER 005 supersession stubs + ORDER 003 stale-Schedule annotations

> **Status:** `complete`
> **Branch:** `claude/order-005-supersede-stubs` · **PR:** #2110
> **📊 Model:** Claude Fable · **Run type:** order · docs
> **Venue:** superbot-next dispatcher, remote container (owner-authorized landing, auto-merge-enabler on green)

Docs-only landing of the prepared ORDER 003 rider + ORDER 005 slice: supersession banners on the
three docs whose living successors moved to fleet-manager, plus stale-reference annotations in
`docs/operations/autonomous-routines.md` so the owner-paused dispatch/night-executor triggers are
no longer presented as live. Trigger disposal itself stays owner-gated (console); this PR is
annotate-and-leave-paused.

## What changed

- **Supersession banners** on the three docs whose living successors moved to fleet-manager
  `projects/superbot-next/`: `docs/owner/trigger-health-order-2026-07-12.md`,
  `docs/planning/fleet-centralization-plan-2026-07-11.md`, `docs/planning/fleet-review-2026-07-11.md`.
- **Stale-reference annotations** in `docs/operations/autonomous-routines.md` — the owner-paused
  dispatch/night-executor triggers are annotated as paused instead of reading as live schedules.
- Orders: ORDER 003 rider (control/inbox.md L30–36 at 6be93a01dae) + ORDER 005 (L79–85 at
  6be93a01dae). Prepared read-only, owner reviewed the patch and authorized the landing;
  rebased onto f8e2313a (upstream delta was dashboard-data only).
- Verified: `python3.10 scripts/check_quality.py --full` green — 13905 passed, 49 skipped,
  2 xfailed. The new banners join the carried-forward cross-repo supersede soft-warning class
  (`docs/current-state.md` § reconciliation notes; idea already logged:
  `ideas/supersede-integrity-cross-repo-tier-2026-07-11.md`).

## 💡 Session idea (Q-0089)

**Local/CI parity for the session gate** — `check_quality.py --full` passed fully green on this
branch *while the card was still born-red* (`in-progress`), because the session-card status gate
runs only in CI. So the one command CLAUDE.md says to run before every push gives a green signal
that does not predict the PR's actual check state during the whole card-first window. A
`check_quality` step (or `--ci-parity` flag) that evaluates the newest card's status and *reports*
"session gate: expected born-red hold" — pass locally, but say so — would make the divergence
visible instead of silent, and would also catch a forgotten flip before the push instead of at the
third CI poll. Observed this session, not hypothetical.

## ⟲ Previous-session review (Q-0102)

The **47th reconciliation pass** (band-#2100, PR #2102,
`.sessions/2026-07-14-reconcile-band2100.md`) called the 5 supersede-banner soft warnings "honest
cross-repo supersessions the in-repo checker can't model" and carried them forward rather than
suppressing them — this session confirms that read from the other side: the ORDER 005 banners land
in exactly that class, and the right durable fix is still the logged cross-repo-tier idea, not
per-PR whack-a-mole. Its ⟲ lesson — *read the band's actual surfaces instead of assuming the
recent pattern* — applied directly here too: the rebase check verified the upstream delta really
was dashboard-only before proceeding, rather than assuming it.

## 📤 Run report

- **Did:** landed the prepared ORDER 003 rider + ORDER 005 docs slice (supersession banners +
  stale-Schedule annotations) as PR #2110 · **Outcome:** shipped (auto-merge-enabler lands on green)
- **Shipped:** #2110 — 4 docs files, +61/−9, docs only; card-first born-red → flip
- **Run type:** `order · docs`
- **⚑ Owner decisions needed:** `none` (landing itself was owner-authorized in a live turn)
- **⚑ Owner manual steps:** trigger disposal for the paused dispatch/night-executor routines stays
  owner-gated at the console — this PR annotates and leaves them paused
- **⚑ Self-initiated:** `none` (the Q-0089 parity idea is captured above, not promoted)
- **↪ Next:** cross-repo supersede-integrity tier
  (`ideas/supersede-integrity-cross-repo-tier-2026-07-11.md`) would retire the recurring soft
  warnings this PR adds to
