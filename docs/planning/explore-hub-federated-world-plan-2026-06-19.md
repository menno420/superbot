# Federated Explore hub — the open-world spine plan (2026-06-19)

> **✅ OWNER DECISION (Q-0182, 2026-06-28, question panel):** the hub starts as a **flat `HubView`
> router** into each game; the **map/biome/location layer stays deferred** (this plan's existing
> sequencing). The other Q-0182 deferred-layer questions (survival-overlay attach · subsystem docking ·
> cross-game-identity richness) were not separately polled — they ride this plan's defaults until that
> layer is greenlit. Canonical: router Q-0182.

> **Status:** `plan` — promoted from [`ideas/explore-hub-federated-world-2026-06-19.md`](../ideas/explore-hub-federated-world-2026-06-19.md)
> by the band-#1140 reconciliation pass under the **idea→plan gate (Q-0172)** and the owner's
> #1140-fire directive ("promote the federated Explore-hub spine first — it homes
> fishing/mining/pets/survival"). **Owner is the designer; the four open design questions
> (Q-0182) are routed for his answer — this plan builds only the parts those answers do not
> gate, and marks the gated layers explicitly.** Source + the binding contracts win.
> **Subsystem:** games (the federated open-world spine).

## 1. Why this is the highest-leverage move

Mining, fishing, pets, and RPG-survival are each planned as **separate lanes** today and all
*want* to plug into a shared world that doesn't exist yet. Defining that world once homes four
gated lanes. The owner's framing: *"each subsystem like mining and fishing should be part of one
world but also feel like their own game."* See the idea doc for the full framing and the
three-XP-track / hybrid-gear model.

This plan does **not** re-decide the world model — it **builds the spine** the model needs and
**defers** every layer the owner's open questions (Q-0182) gate.

## 2. What already exists (verified against source — do not rebuild)

- **`views/mining/explore_hub.py`** — `MiningExploreHubView(HubView)` + `build_explore_hub_embed()`,
  reached as the `mining:explore_hub` sub-hub from `views/mining/main_panel.py` (shipped #1131,
  mining-hub-redesign Option A). Today it is **scoped under the mining hub** and routes to the
  open-world explorer (Fishing / …).
- **`game_xp`** — the shared cross-game XP service (`services/game_xp` + migrations 065/066) with
  leaderboards and depth records. This is the **global** pool the idea's three-track model names.
- **Mining skill tree** — `services/skill_service.py` + `player_skills` (migration 071): the working
  **per-game** skill-tree prototype the federated model generalizes.
- **Fishing v1** — `!fish`/`!fishlog`/`!fishtop` (shipped #1033→#1041, reconciled to the Q-0175
  spec); its next slices are owner-design-gated.
- **`HubView`** base (`views/base.py`) + the back-button/`_rerender` helpers — every hub panel
  extends it (the consistency-linter `back_button`/`panel_base_class` rules enforce this).

The spine is therefore a **re-parenting + extraction** job, not a greenfield build: lift the
explore hub out from under mining into a top-level world hub, and give the world its own seam.

## 3. Scope — what this plan builds (ungated) vs. defers (Q-0182-gated)

| Layer | This plan | Gate |
|---|---|---|
| Top-level **Explore world hub** (the "town square" HubView routing into each game) | **PR 1** | ungated — re-parents existing #1131 view |
| **World registry** seam (each subsystem registers its hub entry — Mine · Fish · …) | **PR 1** | ungated |
| **Global vs. per-game XP split** made explicit in `game_xp` (global pool) + a per-game tree adapter | **PR 2** | ungated — generalizes the mining prototype |
| **Cross-game identity** read surface (one profile characterizing a player across games) | **PR 3** | ungated read-only (Q-0080 stranger-grade) |
| **Hybrid gear** auto-equip-strongest toggle (defaults OFF, prompts on first equip) | deferred | Q-0182 Q3 + per-user config surface (honcho) |
| **Survival/adventure/quest overlay** + difficulty modes | deferred | Q-0182 Q2 (rpg-survival plan) |
| **Map/biome location model** (vs. a flat HubView router) | deferred | Q-0182 Q1 (the hub-shape fork) |

## 4. The build (3 ungated PRs, ~each a real slice)

> **▶ Status (2026-06-20): PR 1 MERGED (#1156) · PR 3 BUILT (this run).** PR 1 shipped
> `services/world_registry.py` (the seam), `views/explore/world_hub.py` (`ExploreWorldHubView` +
> `build_world_hub_embed`, Mine→mining hub · Fish→fishing card), re-parented the mining `🗺️ Explore`
> button (custom_id `mining:explore_hub` preserved) to forward here, retired the
> `views/mining/explore_hub.py` stub it supersedes, and added the `!world` command. **`!explore` was
> kept** for the hidden mining depth-event mechanic — the world hub uses `!world`. Default worlds
> (Mine · Fish) register via `ensure_default_world_entries()`; pets/survival register their own entries
> at setup.
>
> **PR 3 BUILT (2026-06-20, this run) — the read-only cross-game world card.** Shipped
> `services/game_xp_service.world_identity()` (a pure read aggregator: global level from `SUM(xp)` +
> each game's own level from its own XP, with `GAME_LABELS`/`game_display`), `views/explore/world_card.py`
> (`build_world_card_embed`), a `🪪 World Card` button on `ExploreWorldHubView` (in-place edit, mirrors
> the PR-1 openers), and a `!worldcard`/`!mystats` command. Read-only, stranger-grade (an AST test pins
> no mutation/economy import). **Built on existing data** — see the PR 2 reframe below.
>
> **⚠️ PR 2 reframe (verified against source, 2026-06-20):** the "global vs per-game XP" *data layer
> already exists* — `game_xp` is **already keyed per `game`** (`db.add_game_xp(user, guild, game, …)`,
> with `GAME_MINING`/`GAME_CRAFTING`/`GAME_FISHING` constants) and the **level is already global**
> (derived from `db.get_total_xp` = `SUM(xp)` across games). So PR 2's *visibility* half is effectively
> done by PR 3's read surface. PR 2's **remaining** work is only the heavier, design-laden part: a
> **per-game *skill tree*** discriminator on `player_skills` (its PK is `(user, guild, branch)` — no
> `game` column, so fishing can't have its own tree without a **PK migration on a live progression
> table**) **plus** the new "per-game tree fast + global trickle" *earning model* (today game XP feeds
> only the global pool; the two-track-per-game model the plan sketches is a progression-balance change
> the owner-designer should weigh in on). That migration + earning-model decision is why PR 2 stays
> **owner/runtime-verify-gated** — do it in a runtime-verified session with owner design input, not an
> empty autonomous fire. **Next = PR 2** (per-game skill-tree discriminator + earning-model decision,
> gated as above).

### PR 1 — the top-level Explore world hub + world registry

- **New `views/explore/world_hub.py`** — `ExploreWorldHubView(HubView)` + `build_world_hub_embed()`,
  the "town square" you walk out from. It routes to each registered game's entry hub (Mine · Fish ·
  … ). Lift the routing logic from `views/mining/explore_hub.py`; the mining sub-hub button becomes a
  thin forward to the world hub (no behavior change for existing players — the panel still opens).
- **New `services/world_registry.py`** (or `utils/world/registry.py` per the helper-policy read) —
  a small registry where each subsystem registers `WorldEntry(key, label, emoji, open_callback)`.
  Mining and fishing register at setup. This is the seam pets/survival dock into later (Q-0182 Q3).
  Model it on the existing subsystem/hub registration pattern (`scripts/new_subsystem.py` output).
- **New cog command `!explore`** (or re-home the existing one) opens the world hub directly.
- **Tests:** registry registration + de-dup; the world hub renders with the registered entries;
  byte-identical mining sub-hub forward.
- **Arch:** `views/explore/` may import utils/core/services/views (not cogs); the registry lives in
  services/ or utils/ per `docs/helper-policy.md` (read it before placing — a shared registry that
  both cogs and views call belongs below the cog layer).

### PR 2 — make the global vs. per-game XP split explicit

- **`game_xp` becomes the documented global pool**; add a thin **per-game XP adapter** that the
  mining skill tree already instantiates (generalize `skill_service.py`'s point-source so a second
  game — fishing — can adopt it with a config row, not a fork). No new schema if the existing
  `player_skills`/`game_xp` tables suffice; one migration only if a `game_key` discriminator is
  missing (verify the live schema first).
- **Earning split:** every game feeds its own tree (fast) **and** the global pool (slow trickle) —
  wire the trickle at the existing XP-award seam. Keep byte-identical when a game registers no tree.
- **Tests:** global trickle on any game; per-game tree isolation (master miner → fishing tree at zero).

### PR 3 — cross-game identity read surface

- A read-only **`/myprofile`-adjacent "world card"** (or a section on the existing profile card,
  `views/profile/`) characterizing a player across games: global level, per-game levels, signature
  stats. Read-only, stranger-grade (Q-0080). No writes — the auto-equip/gear writes are deferred.

## 5. Sequencing & gates

PR 1 → PR 2 → PR 3 are independent enough to ship in any order, but PR 1 (the hub + registry) is the
keystone the others read. **Stop at PR 3** until the owner answers **Q-0182** — the gated layers
(gear auto-equip, survival overlay, biome map) each need a design decision and at least one of them
(gear toggle) also needs the per-user config surface that the honcho-memory lane owns.

## 6. House-style anchors (so an executor builds it cold)

- HubView + back-button discipline: `views/base.py`, the consistency-linter rules 2/3.
- Subsystem registration pattern: `scripts/new_subsystem.py`, the `/new-subsystem` skill.
- XP seam: `services/game_xp`, `services/skill_service.py`, migration 071.
- Pre-edit: `python3.10 scripts/context_map.py <file>` + `check_architecture.py --mode strict`.

→ relates [explore-hub idea](../ideas/explore-hub-federated-world-2026-06-19.md) ·
[fishing plan](fishing-open-world-expansion-plan-2026-06-18.md) ·
[mining-hub-redesign](mining-hub-redesign-2026-06-15.md) ·
[rpg-survival](rpg-survival-difficulty-design-2026-06-10.md) ·
[pets-companions](pets-companions-plan-2026-06-09.md) · the [games folio](../subsystems/games.md) ·
Q-0182 (the four open design questions) · Q-0175 (fishing) · Q-0080 (stranger-grade).
