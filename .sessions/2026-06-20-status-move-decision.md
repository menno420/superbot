# 2026-06-20 — Status-move decision: self-buffs for v1 (+ expansion direction)

> **Status:** `complete`

## Arc

Owner resolved the one open combat knob (design doc §5): *"original Pokémon also has status moves
that affect your own Pokémon, and healing is usually reserved for certain types/moves, so this is a
more balanced way for now; maybe later we can add more — extra creatures, extra status and attack
moves."* Records the decision + the future-expansion direction. Docs only — the sim already models
self-buffs, so no code/balance change.

## Shipped (PR — design doc)

- **§5** — status-move effect **DECIDED**: both stay **self-buffs** (`+DEF` / `+ATK`) for v1, with
  the owner's rationale (Pokémon-style self-affecting status; healing kept *out* of the universal
  kit as the balance call, reserved as a type-/move-specific effect later). Added a **Future /
  expansion (v2+)** subsection: more creatures (data), more moves (moves likely become data too —
  type-/move-specific healing, debuffs, status conditions), seasons/waves — all additive, each
  sim-revalidated.
- **§2b** — updated the status-move paragraph from "open knob" to the decided self-buff model.

## ⚠️ Process note (born-red slip — own mistake, corrected)

I wrote this card as `complete` in the **first** commit instead of `in-progress`, so PR #1195's
session gate never held — auto-merge fired on the green card-only commit **before** the actual doc
edit (`d1909cd`) landed, and the merge **dropped the doc change** (the #843 race the born-red rule
exists to prevent). Caught it on a post-merge `git grep` verification: the decision text was missing
from `main`. **Re-landed** the dropped doc change via cherry-pick in a follow-up PR. **Lesson (the
rule, restated):** the session card MUST be `in-progress` in the first commit and only flipped to
`complete` in the *final* commit, *after* the real work is staged — writing it `complete` up front
defeats the gate. Always `git grep`-verify a decision actually reached `main` after a docs PR merges.

## Verification

- `check_docs --strict` ✓ · `check_plan_homing` ✓ (39/39) · sim still PLAYABLE (unchanged).

## 💡 Session idea (Q-0089)

**When moves become data (v2), reuse the `creatures.json` pattern: a `moves.json` catalog + a
per-creature `movepool` field, validated by the same sim.** The v1 uniform 4-move kit is the right
start, but the owner's "extra status and attack moves" lane will need movepools; designing it as
data from the outset (not hardcoded `moves_for`) keeps the balance-before-build gate intact for every
new move. Lane = design/tooling. (Captured, not built — it's a v2 concern.)

## ⟲ Previous-session review (Q-0102)

The #1194 combat session correctly *flagged* the status-move effect as the one open knob rather than
silently picking — and the owner's answer confirmed the flagged default (self-buffs) was right, with
a rationale worth preserving (healing-as-universal would be unbalanced). **System improvement:** this
is the "flag the genuine fork, default sensibly, let the owner confirm" loop working as intended —
the default shipped, stayed correct, and the owner's *reasoning* (not just the choice) is now in the
doc so a future agent won't re-open it. No filler change needed.

## 📤 Run report

- **Did:** recorded the owner's status-move decision (self-buffs v1) + the expansion direction ·
  **Outcome:** shipped (docs)
- **Run type:** `manual · owner decision capture`
- **⚑ Owner decisions needed:** none new (Q-0187 a–d still open; this closed the §5 combat knob)
- **⚑ Self-initiated:** no (owner decision)
- **↪ Next:** the creature plan is design-complete; the gated runtime build (Lane A catch, Q-0186)
  is the next real step when the owner greenlights `disbot/` work.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (docs only, auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 |
| Sim/balance change | none (self-buffs already modeled) |
| Open combat knobs remaining | 0 (§5 resolved) |
| New ideas contributed | 1 (`moves.json` data pattern for v2) |
