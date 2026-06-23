# 2026-06-23 — Fishing bait speed knob

> **Status:** `complete`

**Run type:** routine · dispatch

## Arc

Empty-fire dispatch run (no work order). Synced live `main`, oriented (working
agreement → collaboration model → current-state → newest sessions → bug-book),
confirmed the open bugs are gated/owner (BUG-0009 data-gated, BUG-0011 needs a VPS
repro, BUG-0019 #1 owner design fork) and **zero open PRs** in flight. Picked the
S1 ▶ next-startable lane the previous session (bait layer #1329) explicitly teed
up: the **bait speed knob** — owner decision 4 (`fishing-minigame-design` §4)
named "faster bites" the clean future knob on the same `CastStart`/cast-view seam
the rarity knob already uses.

## Shipped (PR #1337)

The bait layer's second economy knob. Bait now carries a `bite_speed` multiplier
(≤ 1 = faster, mirroring `rod.bite_speed`); while a pack is loaded it compounds
onto the rod's bite-wait, so a loaded lure makes fish bite sooner — more casts
within the same energy bar — exactly as `rarity_pull` compounds for catch quality.
Built house-style, mirroring the rarity-knob threading:

- `utils/fishing/bait.py` — `Bait.bite_speed` field; shelf broadened into two
  orthogonal knob families + a combo: rarity baits (worm/grub/lure, speed-neutral),
  speed baits (Live Minnow / Flash Spinner, rarity-neutral), and a premium combo
  (Royal Feast — both). New shared `effect_text(bait)` describes only the knobs a
  bait actually turns (so a speed bait never mislabels itself "×1 rarity").
- `services/fishing_workflow.py` — `begin_cast` computes
  `effective_bite_speed = rod.bite_speed × bait.bite_speed`, exposed on `CastStart`
  (default 1.0); `buy_bait` purchase message now uses `effect_text`.
- `views/fishing/cast_view.py` — `prepare_cast` threads `effective_bite_speed`
  into `FishingCastView`; `_run_bite` paces on the threaded speed (falls back to
  the rod's own when unset, preserving the `!fish`/test path).
- `views/fishing/bait_shop.py` — shop embed + shelf + select show both knobs.
- Tests: catalog invariants (both families exist, every bait improves ≥1 knob,
  valid faster-multiplier, per-family price monotonicity, `effect_text`), workflow
  compounding (rod×bait speed, rod-only without bait), view threading (`_run_bite`
  uses the threaded speed; `prepare_cast` threads it). 62 fishing tests green;
  full mirror **11902 passed**; arch strict 0 errors.

No migration (catalog-only knob; the DB still stores just key + charges), no new
command, **no artifact regen** (no command added → the generated-artifact tests
the bait *layer* session had to regen don't trip here).

## Drift fixed on sight (Q-0166)

The S1-sector "▶ next" + the design plan §3 both flagged "re-tune the #1289 fish
sell values upward" as an open follow-up. It is **stale** — PR **#1304** ("Fishing
minigame PR4: separate energy pacing + generous sell rebalance") already raised
`_fish_value` from 1–7 → 1–21 once the separate energy bar landed, owner-confirmed
via AskUserQuestion. De-staled both: marked the flag DONE (#1304) and closed the
two fishing tuning items in the S1 sector queue.

## Decisions made alone

- **Orthogonal knob families on the shelf** (rarity-only · speed-only · one combo)
  rather than every bait turning both knobs — keeps the pre-cast decision legible
  ("bigger fish, or faster casts?"). Reversible tuning; owner can collapse/expand.
- **Bait `bite_speed` values** (Live Minnow 0.80, Flash Spinner 0.60, Royal Feast
  0.70) + prices (200 / 600 / 1800) are first-pass tuning constants in
  `utils/fishing/bait.py` — tune against live play like the rod ladder.
- `effect_text` lives in `utils/fishing/bait.py` (not the view): both `services`
  (purchase message) and `views` (shop) need it → helper-policy says `utils`.

## Flagged for maintainer

- Unverified half: the live Discord cast/shop UX wasn't exercised (no live bot);
  the logic + the compounding are unit-covered, but a Q-0086-style live walk of
  `!bait` → load a speed bait → cast would confirm the quicker bite *feels* right
  and the shop's two-knob labels read well in-channel.
- Bait tuning constants are first-pass (above) — ratify or adjust after play.

## Context delta

- **Pointed to but didn't need:** the broad orientation route — like the bait-layer
  session, the *sibling fishing seam* (the rarity knob's exact threading
  `rod → begin_cast → CastStart → roll_cast`) was the real template; the speed knob
  is its `view`-time twin (rod → begin_cast → CastStart → `FishingCastView`).
- **Discovered by hand:** the sell-value re-tune flag was already satisfied by
  #1304 — a `git log -S"_fish_value"` settled in one grep what the prose flag left
  ambiguous. Cheap lesson: when a "tuning flag" is vague, check the field's history
  before treating it as open.

## 💡 Session idea (Q-0089)

**Bait auto-reload from your pack** — a small per-player toggle (`!bait auto on`)
that, when your loaded pack runs dry mid-trip, automatically buys the *same* bait
again if you can afford it (and pings once when you can't), so a good fishing
streak isn't broken by re-opening the shop every 10 casts. Pure UX-smoothing on
the existing `buy_bait` seam — no new economy, just fewer menu trips. Genuine
quality-of-life now that bait is a recurring decision; captured here (small enough
to not warrant its own idea file yet — grep `docs/ideas/fishing*` before building).

## ⟲ Previous-session review (Q-0102)

The bait-layer session (#1329) was clean and explicitly teed up *this* knob with
the exact seam to use — that handoff made this run fast (orient → build, no
re-discovery). One genuine miss: it (and the §3 author) left the sell-value
re-tune flagged as open in **two** docs while #1304 had already done it — a small
drift that survived because the flag was prose, not a checkable assertion.
**System improvement surfaced:** "tuning flag" items in plans/sector files have no
done-detection — they sit open until a human re-reads them. A cheap durable guard
would be a convention that a tuning flag names the *symbol* it tunes
(`_fish_value`, `Bait.bite_speed`) so a `git log -S` (or a future linter) can spot
"this flag's symbol last changed in PR #N → likely already addressed." Captured as
the review note rather than built (it's a workflow-tooling idea, not this PR's
lane).

## 📤 Run report

- **Did:** shipped the fishing bait **speed knob** (the design's named second
  economy knob) end-to-end + de-staled the already-done sell-value flag · **Outcome:** shipped
- **Shipped:** #1337 — `Bait.bite_speed` + rod×bait compounding in `begin_cast` →
  `CastStart` → `FishingCastView._run_bite`; speed/combo baits; two-knob shop UI;
  shared `effect_text`; tests; CI green. Plus drift fix: sell-value flag → DONE (#1304).
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none (orthogonal-shelf + the bite_speed/price
  constants are reversible tuning defaults — ratify-if-you-disagree)
- **⚑ Owner manual steps:** none (a merge auto-deploys; no migration, no data seed —
  the knob lives in code, the bait table is unchanged)
- **⚑ Self-initiated:** the *implementation* was an autonomous empty-fire pick of
  the S1 ▶ next-startable fishing follow-up (an existing design plan §4 item teed up
  by #1329, not a fresh idea→plan promotion), so no new plan was created; flagging
  it so the unprompted build is reviewable. The sell-value drift fix was bugs-first
  on-sight (Q-0166), not a new feature.
- **↪ Next:** current-state ▶ Next action sharpened — the two fishing tuning flags
  are now closed; remaining fishing lane is **boat/deepwater** (§5, a real
  multi-PR venue) or the **bait-crafting** idea; other S1 ▶ lanes (Project Moon
  runtime PR1 / botsite React PR2) unchanged.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at write (1 auto-merging on green: #1337) |
| CI-red rounds | 1 (full-suite: black wanted the multi-line catalog tuples reformatted → `black` → green) |
| Repo-rule trips | 0 (arch strict 0 errors) |
| New ideas contributed | 1 (bait auto-reload) |
| Ideas/drift groomed | 1 (sell-value re-tune flag marked DONE #1304 in 2 docs) |
