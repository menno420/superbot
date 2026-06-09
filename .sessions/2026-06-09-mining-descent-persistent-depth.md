# Mining "The Descent" — persistent depth (Wave 1)

**Branch:** `claude/amazing-noether-az3pxz` · **Date:** 2026-06-09

Continued executing the mining plan (brainstorm §7.7 / session log
`2026-06-08-mining-character-platform-foundation.md`). Last session shipped Wave 0 +
the equipment seam (#606); this session built the keystone next slice: **persistent
depth** — the mining "Descent" becomes real, interactive, and biome-aware.

## What shipped
- **Migration `061_mining_player_state`** — `(user_id TEXT, guild_id BIGINT, depth INT,
  updated_at)`, PK `(user_id, guild_id)`. Survival columns (health/stamina) deferred.
- **`utils/db/games/mining_player_state.py`** — direct-lane owner (`get_depth`/`set_depth`),
  re-exported from `utils/db/__init__.py`. Mirrors the equipment seam; no service, no audit
  (mining is intentional direct-lane game state).
- **`cogs/mining/world.py`** — pure depth↔biome + descent-gating model. Reuses one canonical
  `exploration.BIOME_ORDER` (refactored `_BIOME_DEPTH` to derive from it → single source of
  truth, pinned by a test). `biome_for_depth`, `max_accessible_depth`, `can_descend/ascend`,
  `descend/ascend`, `describe_position`, `descend_hint`.
- **Biome threaded through `!explore` + `!mine`** (cog + hub button + MineView): both now resolve
  the player's real biome. `rewards.roll_mine_loot` gained a defaulted `depth` kwarg + a pure
  `ore_weights_for_depth` (depth 0 == legacy table exactly; deeper = richer ore, same four ores).
- **Navigation UX:** `!descend`/`!ascend` commands + hub **Descend/Ascend** buttons (row 2,
  guarded, gated by light). Position shown in explore/mine/descend results + `!minestats`.
- **Tests:** `test_mining_world.py` (14), `test_mining_player_state_db.py` (3),
  `test_mining_descent.py` (2), + extensions to exploration/rewards/navigation/no-root-overview
  tests. Full CI mirror green (8220 passed); arch strict 0 errors.
- **Live-verified:** booted Galaxy Bot#6724 — migration 061 applied, `mining_player_state`
  table correct, MiningCog loaded, 0 ERROR/CRITICAL/Traceback.

## Owner decision made (flagged for confirm)
**Descent gating (§6.8 P2) — DECIDED (reversible agent call).** Depth access is gated by the
equipped light's already-shipped `depth_access` stat and is **persistent, not consumed**:
torch→Cavern (1), lantern→Deep (2); Magma (3) needs gear that doesn't exist yet (headroom).
Chose this over "consume a light per descent" because it reuses the stat gear already feeds,
matches decision 6.1 #3 (persistent position), and leaves consumption to the durability slice
(P5). The whole gate is one pure function — trivially swappable. Recorded in brainstorm §6.8 +
flagged in the PR. **Not blocking; redirect if the owner prefers a consumption model.**

## Learnings / gotchas
- **`| tail` masks the real exit code.** `check_quality.py --full | tail -40` reported the
  pipeline's exit (tail = 0) while pytest had actually failed. Run it as
  `check_quality.py --full > f 2>&1; echo $?` to see the true status. (Bit me once — a hub
  button-count regression test was hiding under a "green" tail.)
- **Pin button-count tests are load-bearing.** `test_mining_no_root_overview` asserts an exact
  hub button count (anti-creep guard); adding Descend/Ascend correctly broke it (6→8). Update
  the count + docstring when intentionally adding buttons; don't just bump the number blindly.
- **Views→cogs stays lazy.** `world` is imported lazily inside every view handler (explore/
  descend/ascend buttons, MineView) — module-level would be a *new* arch-fix-13 violation. The
  cog imports it at module level (cogs→cogs allowed).
- **DB-mock tests must patch every new `db.*` call.** Adding `db.get_depth` to `_handle_mine`
  meant patching `views.mining.mine_view.db.get_depth` in the navigation test, or it hits the
  uninitialised pool.

## Next steps (Wave 1, each its own slice)
Per brainstorm §7.7 + the games folio:
- **Deathmatch reads `EffectiveStats`** — add combat gear (sword/armor → `damage`/`defense`),
  make deathmatch read the stat block instead of hardcoded HP/dmg. Proves the cross-game seam.
- **Sell-ore / buy-gear market** — the cross-domain leg; *this* one routes through
  `economy_service` (genuine audited service, unlike the rest of mining).
- **Audited Workshop + durability + structures** (Forge/Vault/Home).
- Mother-panel refactor (§6.3 live overview showing depth/biome) — the hub embed is still
  static; depth shows only after an action. Noted, not blocking.

## Context delta
- **Needed and well-pointed:** the brainstorm (§6.4 schema, §6.5 seams, §6.8 questions, §7.7
  roadmap) + last session's `.sessions` log gave a turn-key spec for this slice. The
  equipment seam (`mining_equipment.py` + `equipment.py`) was the exact pattern to mirror.
- **Needed, found by hand:** that `explore_from_state` already took a `biome=` param (the prior
  session deliberately left the seam) — only the callers hardcoded Surface. Not stated in the
  plan; found by reading the source. Saved a rewrite.
- **Pointed to but didn't need:** the games/mining/idle roadmap draft + economy/social drafts —
  those route *later* waves; this slice was fully specified by the brainstorm + foundation log.
- **Gap worth promoting:** "how to drive a PersistentView button in a unit test" still isn't in
  a folio (last session noted the same for view callbacks generally). I leaned on source
  inspection (`inspect.getsource`) + the pure-logic split instead. If a third session needs it,
  promote a short "testing Discord views" note into the games folio.
