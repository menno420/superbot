# Session: 3-layer sector map (top layer) + hook-vs-rule decision policy

> **Status:** `complete`

**Branch:** `claude/sector-map-and-hook-policy` · **PR:** TBD · **Date:** 2026-06-14 · **Type:** owner-directed workflow substrate (manual)

## What this session did
Two owner-directed substrate pieces.

### Shipped
1. **`docs/repo-sector-map.md`** — the **3-tap nav top layer**. Owner settled the taxonomy: **5
   sectors** on a **mechanism-vs-content axis** — S1 Bot · S2 BTD6 · **S3 AI-Memory system (the
   *mechanism*, a shippable engine of its own)** · **S4 Documentation system (the *content/product*
   the engine generates)** · S5 Operations. Owner's load-bearing clarification: *"the docs are not
   the system, the docs are a product of the system"* — so Memory and Docs are separate sectors
   (the substrate is the portable engine; the docs are its output). Each sector links down to its
   middle layer (folios) and bottom (cogs/ideas); reconciled with `repo-review-map.md` (planning ≠
   review taxonomy). Q-0137 Thread-3 recorded as DECIDED.
2. **`docs/operations/hook-policy.md`** (Q-0139) — when a fix qualifies as a hook vs. a checker /
   CLAUDE.md rule / settings.json config / doc. Five mechanisms, a five-part test, a quality bar, a
   decision tree, worked examples. The executable-config analogue of `helper-policy.md`. Prompted by
   the Q-0138 freshness hook.
- Wired both into `AGENT_ORIENTATION.md`; bumped the `check_docs` top-level ratchet 18→19 (the one
  sanctioned raise — a genuine top-level nav peer).

### Still open (owner)
- Q-0137 Threads 1 & 2 (Hermes-dispatch-all-but-reconciliation + staged deep-clean) — not yet decided.
- The 3-tap map's **middle/bottom layers** (folio completeness, cog/idea leaf-wiring) — the larger
  nav build, a focused next session.
- Hermes skills: the `skill-author` meta-skill + Hermes→repo skill round-trip (the gap found this
  session) — captured below, not yet built.

## 💡 Session idea (Q-0089)
**`scripts/check_sector_map.py`** — assert every top-level `disbot/` area and every `docs/subsystems/`
folio is reachable from **exactly one** sector in `repo-sector-map.md`, turning the "≤3 taps from
anywhere" promise into a checkable completeness invariant (no orphaned area, no double-homed one).
Small, read-only; the structural guard the new top layer needs. Dedup-checked: `check_docs` covers
doc reachability, not sector-coverage — no overlap.

## ⟲ Previous-session review (Q-0102)
Reviewing the **#857 capture + freshness-hook work:** strong — it turned a real failure (the #857
dirty PR) into a durable guard (the Q-0138 hook) in the same session. **What it missed:** the
freshness hook only checks **your own** current branch; it can't see **other** sessions' PRs sitting
dirty (the original #857 symptom was a *parallel* PR). **System improvement:** the Thread-2 staged
deep-clean should own an explicit **open-PR/branch dirty sweep** (`check_open_pr_branch_health.py`,
the prior session's Q-0089 idea) — the fleet-wide complement to the per-branch hook. Together they
cover both "my branch is stale" and "some PR is rotting."

## Doc audit (Q-0104)
`check_docs --strict` ✓ (ratchet bumped to 19; new docs reachable via orientation + sector-map links) ·
`check_quality --check-only` ✓ (touched `check_docs.py`) · Q-0137 (sectors) DECIDED + Q-0139 recorded.
**Grooming (Q-0015):** settling Q-0137's sector thread + building the map *is* the grooming move —
advanced the captured design idea from DISCUSS to a built top layer.

## Hermes-skills review (carried to next session)
Reviewed the 10 in-repo Hermes skills (`docs/operations/hermes-skills/`). Finding: all are
we-authored; **Hermes-authored skills live on the VPS only — no repo round-trip**, so we can't review
them. Two concrete next builds: a **`skill-author` meta-skill** (guides Hermes to design a new skill
once, correctly, AND commit the source back) + a sharper which-skill-when. Captured for a focused
Hermes session.
