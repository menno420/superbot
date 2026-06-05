# Direct-DB Exception Ledger (RC-8A)

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
| `accepted-direct-write` | A write to a **legacy domain with no `*_mutation.py` owner** (chain, mining, prohibited-words, deathmatch, warnings, role-thresholds, reaction-roles). `utils.db` is the only seam today. | none now; a mutation service is a *future option*, not a current violation |
| `service-migration-required` | A write to a domain that **does** have a mutation-service owner, called directly. AST-enforced (INV-F economy, INV-G xp, INV-E governance, ai-policy); tracked in `mutation_owners.yaml` `known_raw_write_violations`. | must route through the service |

## Ledger — cog → `utils.db` usage (2026-06-05)

| Cog(s) | Representative calls | Class | Notes / owner |
|---|---|---|---|
| `economy_cog`, `economy/_helpers`, `inventory_cog`, `blackjack/*` | `db.get_coins`, `db.get_economy`, `db.get_inventory`, `db.get_xp` | `accepted-read` | **reads only.** Coin/XP **writes** route through `services.economy_service` / the XP service (INV-F/INV-G AST-enforced — no direct coin/xp writes appear in cogs). |
| `chain_cog` | `db.get_chain_channel`, `db.get_all_chain_channels` / `db.set_chain_channel`, `db.set_chain_limit`, `db.delete_chain_channel` | read → `accepted-read`; write → `accepted-direct-write` | No `chain_mutation.py`; `utils.db.chain` is the seam. |
| `mining_cog` | `db.get_mining_inventory` / `db.update_mining_item` | read/write → `accepted-(read/direct-write)` | No mining mutation service. |
| `moderation_cog` | `db.get_prohibited_words` / `db.clear_warnings`, `db.add_prohibited_word`, `db.remove_prohibited_word` | read → `accepted-read`; write → `accepted-direct-write` | Warnings/word-list have no mutation service; mod **actions** are audited separately via `audit_events`. |
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
