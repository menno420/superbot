# Session: dispatch-test fixes — executor dimension + startability tags + S1 freshness

> **Status:** `in-progress`

**Branch:** `claude/ecstatic-euler-bslyvd` · **PR:** (opening) · **Date:** 2026-06-14 · **Type:** owner-directed workflow substrate (docs-only)

## Why (HOLD — born-red card, Q-0133)
A live **dogfooding test** of the 5-sector dispatch structure (owner-requested this session) traced
3 sectors (S1/S2/S5) from "dispatched → ready-to-work." The structure passed on speed (2–3 hops, all
links resolve, the index ranks, a stale `Now` self-corrected at the linked authority in one hop), and
surfaced **3 findings**. The owner chose to **build all 3 into one docs PR** (executor dimension
decided-by-derivation).

### Planned (docs-only — no `disbot/`)
1. **Finding 1 (freshness):** de-drift **S1's `Now`** for #878 (offline eval/smoke matrix SHIPPED →
   next = live half (creds-gated) + Layer B) and **link P1-1's plan** (the hardening roadmap) directly
   from the S1 block.
2. **Finding 2 (non-empty ≠ startable):** add a **startability legend** to the dispatch contract
   (`▶ startable` / `⛔ gated` / `👤 maintainer`) and tag every sector's `Now` items — so a
   dispatcher can see whether to fire an autonomous worker at all (S2's `Now` was non-empty but
   demand-driven/maintainer-only; the startable item was in `Next`).
3. **Finding 3 (executor dimension):** add **who runs it** to the dispatch contract —
   **Claude-in-repo / Hermes-on-VPS / maintainer**. Most sectors default to Claude-in-repo; **S5 is
   the outlier** (Hermes/maintainer). A complete dispatch is **sector + action + executor**.
4. Record the derived decision as **router Q-0143** (refines Q-0137 Thread 1); stamp `current-state.md`.

Homes: `repo-sector-map.md` § dispatch targets (the contract) · `roadmap.md` per-sector `Now` (the
live tags) · router Q-0143 (provenance).
