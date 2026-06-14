# Idea — a slot-carry tracker so the carried-plan-slot escalation fires on data

> **Status:** `ideas` — capture, **not** a plan, **not** approval. Source code and the binding
> contracts win over this file. Lane: workflow / tooling (first-class per CLAUDE.md —
> "improving the orientation/tooling for the next session is first-class work").
> **Raised:** 2026-06-14, the band-#870 Q-0107 reconciliation pass.
> **Provenance/reliability:** a planning-hygiene convenience; verify it actually catches a
> real silent-carry before trusting it, and delete it if a reconciler finds it noisy or wrong
> more than it helps.

## The friction (felt this pass)

The band-#870 pass §6 noticed something only by **manually diffing three consecutive pass
docs**: two planned slots — P1-1's full eval-matrix and the substrate-kit remainder — have
carried *untouched* across #820 → #840 → #870, because both are gated (creds / owner-steered),
while the buffer slot absorbed a large unplanned thread each band. A queue whose top slots never
execute looks like a plan that doesn't work, even though the system ships plenty.

The pass acted on it **by hand**: it added a `gate-state` tag to every slot and an
"escalate to the owner-action list if it carries a fourth band" rule for the substrate-kit
slot. But that rule only fires if a future reconciler **remembers to diff the prior pass docs**
and count carries — exactly the manual, forgettable step the print-subjects / pre-brief ideas
exist to kill for the *ledger* side. The escalation should fire on **data**, not memory.

## The idea

A small stdlib check — `scripts/check_slot_carry.py` (or a mode on an existing recon helper) —
that, given the chain of `docs/planning/reconciliation-pass-*.md` docs, parses each pass's §4
queue table and reports **per recurring slot, how many consecutive bands it has carried
unexecuted** (matched on the slot's scope-anchor text / link target, not its sequence number,
since the `#` column is explicitly not a stable id — Q-0142). Output, e.g.:

```
slot "substrate-kit PR 2 remainder + PR 3"  carried 3 bands (#820→#840→#870)  gate=owner  ⚠ escalate
slot "P1-1 eval-matrix (full/live)"         carried 3 bands                    gate=creds  ⚠ split: ship offline half
```

The reconciliation routine reads this at pass start; any slot at the escalation threshold is a
**forced** §3/§6 action (escalate to the owner-action list, split the gated half off, or
explicitly re-justify the carry) instead of a thing a sharp reader might notice. It turns the
band-#870 §6 escalation rule into a self-firing guard — the same move the open-PR-with-state
snapshot made for stale PRs, applied to stale *plan slots*.

## Why it's worth having

- The whole point of the loop is that recurring realities become **structured, diff-able
  artifacts**, not things each pass re-derives by eye. The slot-carry pattern was invisible
  across three pass docs until a manual diff surfaced it; this makes it visible every pass.
- It directly protects against the failure mode the owner cares about most — owner-steered or
  gated work **silently rotting** in a plan that keeps re-listing it (the plan-slot cousin of
  the #766/#771 stale-PR rot the snapshot already guards against).
- Cheap and bounded: pure text parsing over docs the routine already has; no runtime touch.

## Composes with

- [`ledger-checker-print-pr-subjects`](./ledger-checker-print-pr-subjects-2026-06-14.md) (✅ #864)
  and [`reconciliation-prebrief-at-session-start`](./reconciliation-prebrief-at-session-start-2026-06-14.md)
  — same family: kill the manual derivation a reconciler does by hand before real thinking
  starts. This one targets the **plan side**; those target the **ledger side**.

## Scope note

Runtime-lane (a new `scripts/` check + routine wiring), so **out of scope for a docs-only
reconciliation pass** — captured here for a tooling-lane session to pick up (band-#870 queue
is the natural home, alongside the print-subjects/pre-brief family).
