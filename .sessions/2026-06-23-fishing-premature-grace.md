# 2026-06-23 — Fishing: the `premature_grace` rod knob (the design's 5th knob)

> **Status:** `complete` — routine dispatch run, no work order → advanced the next plan slice. PR #1365,
> auto-merge armed on green (Q-0127); self-initiated promotion of a designed-but-unbuilt knob (Q-0172).

> **Run type:** `routine · dispatch`

## What I'm about to do

Fake-out bites are already shipped (`minigame.roll_fakeout` + the cast view's "you reeled too early —
the fish darted off" penalty). The fishing design
(`docs/planning/fishing-minigame-design-2026-06-22.md`) names a **fifth rod knob, `premature_grace`**,
that fake-outs were meant to "make meaningful" — but it was never built: every rod is equally, harshly
punished for an early reel. This slice adds it.

`premature_grace` (0…1) = the chance a **premature reel is forgiven** (the fish isn't spooked; the cast
survives and the real bite still comes). One forgiveness per cast (so it rescues an itchy-finger slip,
never rewards button-mashing). Scales up the ladder: bare 0.0 → diamond. Pure roll in
`utils/fishing/minigame.py`; the knob on `Rod` (`utils/fishing/rods.py`); the view spends the grace in
`views/fishing/cast_view.py`; surfaced in the rod-shop knob summary.

Also folding in **drift fixes I can see** (Q-0166): the S1 `▶ Next startable` line lists fake-out bites
as *remaining* when it shipped; the design "Other ideas" fake-out bullet isn't marked shipped; and 7
stale claim files for already-merged PRs (#1294/#1322/etc.) need GC.

## What shipped

The design's **fifth rod knob, `premature_grace`**, built end-to-end:

- **`disbot/utils/fishing/rods.py`** — `Rod.premature_grace: float` (0…1) + ladder values
  (bare 0.0 · bronze 0.15 · silver 0.30 · gold 0.45 · diamond 0.60) + docstring (4→5 knobs).
- **`disbot/utils/fishing/minigame.py`** — `roll_premature_grace(grace, rng)` (pure; `≤0` never
  forgives, `≥1` always does, else a `grace`-probability roll).
- **`disbot/views/fishing/cast_view.py`** — a `_grace_used` flag; on a **premature** reel
  (pre-bite, `_PHASE_BITE`), spend one grace: on success the cast survives (not resolved, guard
  held, the still-running bite task arms the real bite) with a reassuring "the {rod} steadies it"
  edit; on failure / grace-already-spent, spook as before. Bare rod (grace 0) never forgives.
- **`disbot/views/fishing/rod_shop.py`** — the knob summary now advertises "N% chance to forgive an
  early reel".
- **Tests** — rods (starter-neutral + monotonic-up-the-ladder + 0…1 range) · minigame
  (`roll_premature_grace` zero/one/probability) · cast-view (forgiven-once · grace-spent-then-spook ·
  bare-rod-never-forgives). Full suite **12093 passed**; mypy clean; arch 0 errors.

**Drift fixed on sight (Q-0166):**
- `docs/current-state/S1-bot.md` ▶ Next startable no longer lists fake-out bites as remaining (shipped)
  and notes the new knob.
- `docs/planning/fishing-minigame-design-2026-06-22.md` "Other ideas" fake-out bullet marked shipped +
  the now-built `premature_grace` knob.
- GC'd 7 stale claim files for already-merged PRs (#1294/#1322/help-* /sleepy-allen/peaceful-franklin).

## Findings / decisions

- **Fake-out bites were already shipped** (`roll_fakeout` + the cast view's early-reel penalty); the
  remaining gap was the `premature_grace` knob the design named but nobody built — so this slice closes
  the design's fifth-knob loop rather than re-doing fake-outs.
- **One grace per cast, by a flag (not a per-press probability)** — a probabilistic-per-press grace
  would let a masher brute-force forgiveness; spending it once makes it rescue an itchy-finger slip
  while leaving button-mashing punished. The flag short-circuits *before* the roll (asserted in tests).
- No workflow/DB change needed: the view already receives the equipped `Rod`, so it reads
  `self.rod.premature_grace` directly.

## 💡 Session idea

**A rod-knob completeness invariant** — a tiny CI test that asserts every field on the `Rod` dataclass
is (a) surfaced in the rod-shop `_knob_summary` and (b) actually *read* somewhere in `cast_view` /
`minigame`. This whole slice existed because a knob (`premature_grace`) was *designed and named* but
never wired — the dataclass would have happily carried an unused field forever. An invariant that fails
when a `Rod` knob has no consumer would have surfaced "this knob does nothing" immediately. (Dedup: the
existing fishing tests check knob *values*, not knob *consumption*; this is the wiring sibling.)

## ⟲ Previous-session review (Q-0102)

The previous session (#1350, remove the cleanup whitelist) was clean, decisive owner-directed work and
its own review made the sharp "delete vs. migrate legacy cruft" point — good. What it (and the chain
before it) *missed* is the inverse class this session hit: **designed-but-never-wired** features. The
fishing design doc listed `premature_grace` as a knob fake-outs "make meaningful," fake-outs shipped,
but the knob silently never did — and three reconciliation passes since didn't catch it because nothing
checks design-doc promises against shipped knobs. **System improvement (initiated):** the rod-knob
completeness invariant above is the mechanical half; the judgment half is that a "✅ SHIPPED" annotation
on a design bullet should be verified against *all* of its named sub-parts, not just the headline
mechanic. I de-drifted the design doc's fake-out bullet to make the knob's status explicit so the next
reader sees the whole promise was kept.

## 📤 Run report

- **Did:** Built the `premature_grace` fishing rod knob (the design's 5th, designed-but-never-wired) —
  forgives one premature reel per cast, scaling up the ladder — + fixed fishing-design/S1 drift + GC'd 7
  stale claims · **Outcome:** shipped (PR #1365, auto-merge armed on green)
- **Shipped:** #1365 — fishing `premature_grace` rod knob + drift fixes
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — merged = deployed (Railway auto-redeploys `worker` on merge; no
  migration, no data step). Knob values (0.0→0.60) are conservative tuning constants, tunable later.
- **⚑ Self-initiated:** yes — no work order this run; promoted the designed-but-unbuilt `premature_grace`
  knob (named in the fishing design doc) to implementation (Q-0172). Reversible; pure-logic + view-gated.
- **↪ Next:** fishing remaining ▶ = open-world expansion Phase 2+ (a multi-PR plan) · shore-cap-at-12
  rebalance (owner balance call). Other startable lanes: Project Moon runtime PR 1, botsite React PR 2.

## ⟳ Doc audit (Q-0104)

`check_quality --full` green (12093 passed); arch 0 errors. The design doc + S1 live state de-drifted
in this PR. PR #1365 isn't in `current-state` Recently-shipped yet (benign newest-merge lag — the next
reconciliation pass at #1380 records it; recon not due this run, Q-0124). No new owner decisions to
route to the question router.
