# Session: Mining hub UX overhaul (in-place cards · sub-hubs · 3-layer menu doctrine)

> **Status:** `complete` — PR #911; born-red card flipped as the deliberate final step (Q-0133),
> which fires native auto-merge on green Code Quality. Owner ended the session at ~800K context.

**Branch:** `claude/amazing-volta-auxt2d` · **Date:** 2026-06-15 · **Type:** UX (S1 Bot · games/mining) — live, owner-steered

## What this did

A large, owner-steered **mining-hub UX overhaul**, built and verified **live on the test bot
(Galaxy Bot#6724)** across the session (the owner tested each step). All on PR #911, `check_quality
--full` green at each stage (final 9835).

- **In-place image cards** — the inventory card + gear paper-doll rendered as separate stacking
  ephemerals; now they ride the panel's own message (`safe_edit(attachments=…)`), cleared on
  navigate-away. Owner-verified ("the gear command is much better").
- **Hub declutter → sub-hubs (Option A, owner-picked from rendered mockups)** — main hub 16 → 12
  buttons: a new **Workshop sub-hub** (Craft · Repair · Forge · Market) absorbed the scattered
  production/economy buttons; **Build/Craft/Recipes consolidated** into one **Craft** entry; child
  panels' Back now returns to the Workshop hub.
- **The 3-layer menu doctrine** — the recipe browser became **Category → Type → Variant**
  (Weapons/Armour/Tools → Swords/Helmets → tier variants), then the **market too**. Codified as a
  **binding standard** in `docs/building-roadmap/hub-ui-standard.md` (owner: "this should be standard
  for any menu") + a shared `utils/mining/taxonomy.py` (one source — craft + buy can't drift).
- **Ordering + a small gameplay change** — variants order by **rarity** (`equipment.material_rank`),
  armour types **head-to-toe**, **shields moved to Weapons** + gained a gentle **damage bonus**
  (1/1/2/2/2; base shield stays defense-only; diamond tuned to +2 to keep the duel-sim band).
- **Compact stat previews** (`equipment.describe_stats_compact`: `⚔️+6` / `⚔️+1 🛡️+3 ❤️+14`) on every
  craftable + buyable item, in embeds and pickers.

Docs: hub-ui-standard doctrine · `planning/mining-hub-redesign-2026-06-15.md` · gear-set-numbers
shield note · roadmap link.

## Context delta

- **Live iteration was the mode** — the owner re-paste a working test-bot token (the env
  `DISCORD_BOT_TOKEN_PRODUCTION` was malformed/truncated → 401; **flag for the owner**: fix the env
  secret so future sessions boot without a chat paste, and rotate the chat-pasted one). Booting +
  rebooting per change drove fast, correct results — by far the most effective loop this session.
- **Boot/kill gotcha (reconfirmed):** `pgrep -f disbot/bot1` matches the *agent's own shell* (its
  command text contains the path) — a plain `kill $(pgrep …)` self-kills the shell (exit 144). The
  journal's comm-checked loop is correct; its `pgrep … && echo "still running"` *also* matches the
  shell, so "still running" can be a false positive. Verify a stop with the comm filter, not bare pgrep.
- The 3-layer doctrine emerged *from the work* (the owner spotted the recurring pattern), then was
  generalised back into a standard — the system-improving loop working as intended.
- **Process miss → fix.** I declared "auto-merge on green" without verifying #911 was *mergeable* —
  parallel mining work (#910 Home, #912 E/F) had landed on `main`, so a real conflict silently parked
  the PR (native auto-merge can't run, and webhooks don't deliver conflict transitions). Resolved the
  merge, and — owner-directed in-session — added a **merge-conflict guard to the Stop hook**
  (`scripts/claude_stop_check.py`: `git merge-tree --write-tree` vs a freshly-fetched `origin/main`,
  hard-fails on a genuine conflict) so a conflicting branch can't be declared done silently again.
  The journal's "verify a stop with the comm filter, not bare pgrep" + "check mergeable state" are
  now partly enforced, not just advisory.

## 💡 Session idea (Q-0089)

**A generic `ThreeLayerBrowserView`.** This session shared the *taxonomy* (data grouping) between the
recipe + market browsers, but the *view navigation* (Category/Type/Variant selects + `render` +
per-level back) is still duplicated across the two. A small generic browser parametrised by
`(item names, leaf-option builder, leaf action)` would DRY the view layer too, so any subsystem gets a
doctrine-compliant 3-layer menu for free (BTD6 towers, settings groups, role pickers…). Captures the
doctrine in code, not just docs. (Dedup-checked: the doctrine + taxonomy are new this session; no
existing idea covers a generic browser view.)

## ⟲ Previous-session review (Q-0102)

The band-#900 reconciliation (#900) planned a tidy "decade queue" of `ready` slots (Character hub,
P1-3 invariants, …) — but, as its own §6 predicted for the **fourth** band running, the actual band
became **owner-live-steered product work** (this entire mining overhaul), not the planned slots. It
did that *well* (the queue's gate-state tags are useful), but the recurring miss is treating
owner-live product work as "buffer/overflow" rather than a first-class, *planned* lane. **Improvement:**
the reconciliation template should carry an explicit **"owner live-steer lane"** sized from history
(it has been the band 4×), so the decade queue stops over-stating plannable capacity. (This is the
band-#900 §6 forward idea — worth promoting from observation to template change.)

## Documentation audit (Q-0104)

- This session's work is in its durable homes: the **doctrine** (hub-ui-standard.md, binding),
  the **redesign plan**, the **gear-numbers** shield note, the **roadmap** link. ✓ (`check_docs
  --strict` green.)
- **Ledger drift (next reconciliation, not this session's):** `check_current_state_ledger --strict`
  flags **#902 · #904 · #907 · #908** (parallel-session loop/docs PRs) missing from Recently-shipped,
  and Recently-shipped is ~2 over the ratchet. Not a CI gate; left for the #930 reconciliation to
  reconcile + archive. PR #911's own ledger entry lands when it merges (next session reconciles).

## Handoff — next session

1. **Character hub** (the one declutter increment left): Inventory/Stats/Skills/Vault → a new
   `MiningCharacterHubView` (mirrors `workshop_hub.py`), `character_btn` opens it, removing those 4
   buttons (main hub 12 → 8). Extract `build_inventory_embed`/`build_stats_embed` + the inventory
   image render into `character_panel.py`; retarget `skills_panel`/`vault_panel` Back → Character hub.
   Update `test_mining_inplace_cards.py` (inventory moves off the main hub). Turn-key in
   `planning/mining-hub-redesign-2026-06-15.md`.
2. **Grid Mine** (needs the owner's v1 sign-off first): N/S/E/W + Up/Down grid movement replacing
   linear depth + Descend/Ascend → main hub reaches the target 6. New world model — design it with
   the owner (size, cell contents, z=depth/light).
3. **Open-world Explore** (fishing/quests) — owner-defined later; stub for now.
4. **Owner action:** fix the `DISCORD_BOT_TOKEN_PRODUCTION` env secret (malformed) + rotate the
   chat-pasted token.
5. Optional cleanup: `market.shop_sections()` is now unused (prunable).
