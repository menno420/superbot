# Direct-DB Exception Ledger (RC-8A)

> **Status:** `reference` — Ledger of sanctioned direct-DB exceptions.

> Companion to `docs/ownership.md` and `architecture_rules/mutation_owners.yaml`.
> Catalogs every place a **cog** reaches the database through `utils.db`
> directly, and classifies it, so new drift is visible.
>
> The binding rule (`.claude/CLAUDE.md`): cogs MAY **read** through
> `utils.db.*`; **writes to a domain that has a `*_mutation.py` service MUST go
> through that service** (AST-enforced for economy / xp / governance / ai-policy).
>
> **Date:** 2026-06-05. Method: `grep -rhoE "\bdb\.[a-z_]+\(" disbot/cogs/` plus a
> check of `disbot/services/` for a matching `*_mutation.py` owner per domain.

This is the **docs-first** half of RC-8 (the thin-cog program). The mechanical
view-move sweep and any new per-domain mutation service are separate, staged
follow-ups (roadmap PR 8) — explicitly **not** done here.

## Classification scheme

| Class | Meaning | Action |
|---|---|---|
| `accepted-read` | A read via `utils.db.*`. The sanctioned read path. | none |
| `accepted-direct-write` | A write to a **legacy domain with no `*_mutation.py` owner** (chain, mining, prohibited-words, deathmatch, role-thresholds, reaction-roles). `utils.db` is the only seam today. | none now; a mutation service is a *future option*, not a current violation |
| `service-migration-required` | A write to a domain that **does** have a mutation-service owner, called directly. AST-enforced (INV-F economy, INV-G xp, INV-E governance, ai-policy); tracked in `mutation_owners.yaml` `known_raw_write_violations`. | must route through the service |

## Ledger — cog → `utils.db` usage (2026-06-05)

| Cog(s) | Representative calls | Class | Notes / owner |
|---|---|---|---|
| `economy_cog`, `economy/_helpers`, `inventory_cog`, `blackjack/*` | `db.get_coins`, `db.get_economy`, `db.get_inventory`, `db.get_xp` | `accepted-read` | **reads only.** Coin/XP **writes** route through `services.economy_service` / the XP service (INV-F/INV-G AST-enforced — no direct coin/xp writes appear in cogs). |
| `chain_cog` | `db.get_chain_channel`, `db.get_all_chain_channels` / `db.set_chain_channel`, `db.set_chain_limit`, `db.delete_chain_channel` | read → `accepted-read`; write → `accepted-direct-write` | No `chain_mutation.py`; `utils.db.chain` is the seam. |
| `mining_cog` | `db.get_mining_inventory` / `db.update_mining_item` | read/write → `accepted-(read/direct-write)` | No mining mutation service. |
| `moderation_cog` | `db.get_mod_logs` (read only) | `accepted-read` | **Since #521 (PR1) warnings/mod-actions have a mutation-service owner:** `warn`/`timeout`/`kick`/`ban`/`unban`/`clear_warnings` route through `services.moderation_service`, and `db.add_warning`/`clear_warnings`/`log_mod_action` are AST-forbidden in the moderation surfaces (`test_no_direct_moderation_writes.py`). The only direct `db.*` left in the cog is the read `db.get_mod_logs`. (Prohibited-word writes live in `cleanup_cog`, not here.) |
| role thresholds (`role_cog` et al.) | `db.get_role_thresholds` / `db.set_role_threshold` | read/write → `accepted-(read/direct-write)` | Legacy role-threshold table; no mutation service. |
| deathmatch | `db.update_deathmatch` | `accepted-direct-write` | Game stat counter; no mutation service. |
| reaction roles | `db.get_reaction_role` | `accepted-read` | — |
| `cleanup_cog`, `counting_cog` | `db.fetchall` + domain reads | `accepted-read` | Counting **state** is written via the cog's managed-task save path (RC-15), not a raw cog write. |

## Findings

- **No `service-migration-required` violations were found in cogs in this pass.**
  The owned-domain writes (economy coins, XP, governance, AI policy) are
  AST-enforced and absent from cogs — consistent with `check_architecture.py`
  reporting 0 errors. Every direct **write** that exists is to a legacy domain
  with no mutation-service owner (`accepted-direct-write`).
- **Update (#521 / server-management PR1):** **moderation** moved from the
  `accepted-direct-write` legacy set into the AST-enforced service-owned set.
  `services.moderation_service` now owns warn/timeout/kick/ban/unban/clear-warnings
  (and system `auto_delete`); direct `db.add_warning`/`clear_warnings`/`log_mod_action`
  in the moderation surfaces is pinned out by `test_no_direct_moderation_writes.py`.
- The cog `utils.db` **reads** are the sanctioned read path and need no change.
- Lazy `views → cogs` import edges surfaced by `check_architecture.py
  --report-lazy-imports` (RC-1, #515) are a *separate* RC-8 backlog (view-move
  sweep), not direct-DB calls — tracked there, not here.

## Cross-references

- `docs/ownership.md` — mutation authority + the Direct-DB **blocklist** (the
  forbidden owned-domain writes).
- `architecture_rules/mutation_owners.yaml` — the enforced blocklist +
  `known_raw_write_violations` (raw-write tech-debt tracking).
- `tests/unit/invariants/test_inv_f_economy_service.py` — the AST scanner that
  keeps owned-domain writes out of cogs.
