# 2026-06-17 — BTD6 roster floor: boss roster + per-difficulty map filter

> **Status:** `in-progress`

## What I'm about to do

Scheduled dispatch fire, **empty work order**. The night queue
(`planning/night-queue-2026-06-16.md`) is **fully consumed** and both open PRs
(#941 image-mod, #929 security tiers) are `needs-hermes-review`-gated. So I take a
fresh slice of the proven, ungated, factory-pattern **BTD6 deterministic floor**
lane (Q-0048, closes the BUG-0009 wrong-assembly class).

Two genuine gaps found in the existing `deterministic_roster_reply` floor
(`disbot/services/btd6_context_service.py`):

1. **No boss roster.** "list all bosses" / "what bosses are in BTD6" falls through
   to the model, which can omit/add one (there are exactly 7:
   Blastapopoulos, Bloonarius, Diamondback, Dreadbloon, Lych, Phayze, Vortex).
2. **"list all expert maps" dumps all 86 maps** grouped by difficulty instead of
   the 13 Expert ones — a wrong-assembly miss when a difficulty is named.

Both are fixed at the root in the same floor function (boss enumeration branch +
per-difficulty filter in `_map_roster_reply`). Tests + ledger to follow.

## Next (PR 2 candidate)
Reassess for a second genuine slice after PR 1 lands (e.g. boss immunity roster).
