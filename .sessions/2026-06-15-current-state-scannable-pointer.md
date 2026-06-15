# Session — current-state.md scannable ▶ pointer + stamp-line archive

> **Status:** `complete`

## Why (a live gpt-5.4-mini calibration finding)

While calibrating Hermes (now on gpt-5.4-mini) with a grounding probe — *"sync, read current-state.md,
name the next ▶ startable slice"* — it **read the real file** (big win over the old weak model) but
**cited a dated reconciliation stamp-line** ("next ▶ = mining Forge") instead of the live pointer, and
so named an **already-shipped** slice (Forge = #905). Root cause is partly the **doc**: the live ▶
pointer was a single ~600-word paragraph, and the `Last updated:` block had **15 re-accumulated dated
stamp entries** each containing a "next ▶ =" string — a trap for any reader, human or model.

## What changed (docs-only, owner-approved "both fixes")

1. **Scannable live pointer** — prepended a one-line **▶ NEXT (live — read THIS line)** lead to the
   `current-state.md` pointer callout naming the actual next step (BUG-0009 slice 2 → security tiers),
   with an explicit signpost: *the live next-step is THIS line, not any other "next ▶ =" lower down or
   in the dated stamps (which are historical) — uses the Forge-#905 stamp as the cautionary example.*
   Directly removes the exact ambiguity Hermes fell into.
2. **Archived the re-accumulated stamp wall** — moved the 72 lines of **2026-06-13-and-older** dated
   `Last updated:` stamps into `current-state-archive.md` § "Stamp-line history" (newest-first, above
   the existing 2026-06-10 entry), per the documented archive convention that had lapsed. The live
   `Last updated:` block now keeps only 2026-06-15 + 2026-06-14.

## Verification

`python3.10 scripts/check_docs.py --strict` green (the 21-vs-20 Recently-shipped note is a pre-existing
**soft** warning from #924's session, untouched here). Stamp move done via an asserted splice (boundary
asserts on lines 155/156/227); archive newest-first preserved.

## 💡 Session idea (Q-0089)

The calibration loop should be **repeatable**: a tiny `superbot-calibration` Hermes skill bundling the
5 probe tasks + "what good looks like", so any session can re-score the control-plane model in 10
minutes after a model/prompt change (this run found a real doc bug *and* a model-judgment gap from one
probe). Pairs with the `hermes-base-hygiene` idea from the prior session card.

## ⟲ Previous-session review (Q-0102)

Prior PR (#923, this same working session) re-tuned the Hermes base for gpt-5.4-mini and added the
calibration probe — and **running** that probe immediately paid off by surfacing this `current-state.md`
trap. Did well: the probe was concrete enough to expose a real failure on the first task. Improvement it
proves: findings from a calibration probe should feed straight back into doc/prompt fixes (done here) —
the probe is only worth running if its findings get actioned, which is the self-auditing loop working.
