# Reconciliation pass — 2026-06-22 · the band-#1290 Q-0107 cadence pass

> **Status:** `historical` — superseded by [the band-#1320 pass](reconciliation-pass-2026-06-22-band1320.md).
> The docs-only review + planning pass for the band that crossed **#1290**
> (cadence = every **30th** merged PR per Q-0134; `#1290 = 30 × 43`; previous cadence pass
> [the band-#1260 pass](reconciliation-pass-2026-06-21-band1260.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1292**
> (`.github/workflows/reconciliation-trigger.yml`) — the **eighteenth** consecutive real cadence fire
> and live proof the loop self-fires: #1292 was authored by **`menno420`** (the `ROUTINE_PAT` owner),
> not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed + control-plane
> · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker → **#1291**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**Merged since the band-#1260 pass (band #1265–#1291; #1264 = the trigger issue, #1266 = the prior pass
itself, #1277 closed-unmerged).** The headline is an **owner-steered mining-platform arc**: the descent
game became a real **(x,y,z) seed-deterministic grid world** with unified dig-as-movement, then got a
stdlib **economy/balance simulator** and a **sim-pinned rebalance + energy system** (food/booster/campfire
refill). Alongside it, a cluster of **CI / autonomous-loop reliability** root-fixes and the **Q-0195
coordination-file restructure** (per-claim + per-sector files) landed. From the planned band-#1260 queue,
only **B1 Starboard PR 2** (#1270) executed — the rest of the band was the buffer becoming the band, the
recurring pattern.

- **Mining — grid Mine + economy/energy rebalance (#1281 · #1282 · #1284 · #1286 · #1289).** The descent
  game became a **(x,y,z) seed-deterministic grid world** with 6-direction movement (hub-redesign PR 3,
  #1281, migration 085), then **unified dig + move** so each directional dig moves you into the cell (#1282);
  a stdlib **economy/balance simulator** (`tools/game_sim/mining_economy_sim.py`, #1284) found a fun/balanced
  reward config, which drove the **sim-pinned rebalance + energy system** (food/booster refill, #1286) and
  **cook + sell fish** energy refill via a campfire (#1289).
- **Starboard PR 2 + creature PvP + BTD6 buff-uptime (#1270 · #1265 · #1268).** Starboard PR 2 — self-star
  exclusion + ignore-channels + the `BaseView` config panel (#1270, the planned B1 slice, builds on #1259);
  creature PvP gained a ⌛ **challenge-expiry timeout notice** (#1265); BTD6 buff-uptime now models
  **attack-speed buffs on the Alchemist** (`alch_speed`, #1268).
- **CI / autonomous-loop reliability (#1275 · #1288 · #1280).** Root-fixed the **CI-strand** class:
  `code-quality`'s `cancel-in-progress` was dropping the *head-commit* run (#1275), and a new
  **`ci-rerun-watchdog`** re-kicks `code-quality` when GitHub drops the `synchronize` event (#1288,
  `check_ci_coverage.py`); plus a **wrong-branch guard** hook that institutionalizes the friction→guard
  reflex (#1280).
- **Coordination-file restructure (Q-0195) + workflow tooling (#1283 · #1285 · #1271).** The
  **state-file restructure** — `active-work.md` → one-file-per-claim (kills the merge-conflict class) +
  `current-state.md` → per-sector files under `current-state/` (#1283, justified by
  `tools/sim/claim_layout_sim.py`); an **unattended-fit dimension** added to the per-sector dispatch
  contract so empty-fire runs stop stalling (#1285); and `band_pr_status.py --themes` — a grouped-entry
  skeleton drafter for this very pass (#1271).
- **Bug fixes — dashboard determinism + command scanner (#1267 · #1291 · #1272).** Root-caused the
  dashboard `generated_at` nondeterminism — deterministic timestamp + refresh self-heal (#1267) and then a
  **hermetic determinism test** that kills the `-n auto` flake (BUG-0024, #1291); BUG-0023 root fix — the
  command scanner now discovers `app_commands.Group` attribute slash commands (#1272).
- **Docs / chore / config + dashboard refresh (#1276 · #1278 · #1274 · #1269 · #1273 · #1287).** Repo
  navigation cleanup + prune the stale claim ledger (#1276); deleted the disproven "synchronize doesn't
  re-fire CI" journal claim (#1278); allow read-only network probes (`curl`) in settings + prune a stale
  claim (#1274); and the per-source-merge `dashboard-data-refresh` cadence regen (#1269 · #1273 · #1287,
  Q-0167).

**Ledger reconciled:** `check_current_state_ledger --strict` flagged 23 merged PRs newer than the #1263
marker (benign-lag class). All of #1265–#1291 were absent from the live ledger; recorded as six grouped
Recently-shipped entries, then ran `trim_recently_shipped.py --apply` to move the oldest bands to
`current-state-archive.md` and recompute the floor pointer. `--strict` green afterward; `check_docs
--strict` green.

**Control-plane reconciled (Q-0135):** `check_loop_health.py` reported SKIP (`gh`/`GITHUB_TOKEN`
unavailable in-container). Manual fallback per Q-0135: the trigger issue **#1292** was authored by
**`menno420`** (a real-user login, not `github-actions[bot]`) → **ROUTINE_PAT is set and the loop
self-fires**. The canonical [Control-plane state table](../operations/autonomous-routines.md) already
records this; no drift to fix this pass (the pointer-only design held).

**Open-PR disposition (Q-0125):** two open PRs, both correctly parked — no action needed.
- **#1290** Help-menu regrouping — **owner-directed, born-red, opened ~20 min before this pass**; an
  active in-flight session. Leave it (Q-0124: do not touch another session's live work).
- **#1279** Reaction-roles PR 6 (PIL banner cards) — `needs-hermes-review` carve-out, self-initiated;
  left for Hermes review (never auto-armed). Leave it.

## 2. Band scorecard (band-#1260 queue → what executed)

| Planned slice (band-#1260) | Outcome this band |
|---|---|
| A1 Project Moon runtime PR 1 (seam) | not started — carries |
| A2 Project Moon first ingest | not started — carries |
| **B1 Starboard PR 2 — config panel** | ✅ **#1270** |
| B2 Creature leaderboards UI + ranked | partial — only the PvP expiry-notice (#1265) landed; the UI carries |
| C1 botsite React-SPA migration | not started — carries |
| C2 Consistency-linter AI-nav PR 1 | not started — carries |
| C3 procedures→skills Batch 2 | not started — carries |
| D1 Reaction-roles PR 6 — PIL cards | 🟡 in flight (#1279, `needs-hermes-review`) |
| D2 Callout-trim actuator | not started — carries |
| E1 Pokétwo/MusicBot mapped features | not started — carries |

**Buffer that became the band:** the mining grid/economy arc (#1281/#1282/#1284/#1286/#1289), the CI
reliability cluster (#1275/#1288/#1280), the Q-0195 coordination-file restructure (#1283), and the
dashboard-determinism bug fixes (#1267/#1291/#1272). ~1/10 planned slots executed — the queue was again
out-paced by owner-steered + bugs-first work, exactly the documented pattern.

## 3. Pruned / fixed + control-plane

- Re-badged the [band-#1260 pass record](reconciliation-pass-2026-06-21-band1260.md) → `historical`.
- Reset the `Last reconciliation pass` marker in `current-state.md`: #1263 → **#1291**.
- Updated the S4-docs sector file: twentieth pass recorded; next recon due once merged PRs cross **#1320**.
- Regenerated `dashboard/data/dashboard.json` (`export_dashboard_data.py`); `check_dashboard_data --drift`
  reported 0 warnings (49 cogs validated) — the artifact was already fresh, but the cadence regen keeps it
  pinned to source.
- No control-plane table drift (the pointer-only design held since the band-#930 fix).

## 4. The next band (depth to #1320)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** Most of the
band-#1260 queue carries forward intact (only B1 executed), and the band *added* buildable lanes: the
mining grid-redesign follow-ups and the owner's in-flight **Help-menu regrouping** (#1290). **Honest caveat
(carried, unchanged):** the *cleanly-ungated self-merge* subset is thinner than the headline — Project
Moon's runtime build and the AI-nav / procedures→skills batches are runtime / `needs-hermes-review`, so an
empty *autonomous* fire should prefer a substantial review-gated lane or promote a fresh idea → plan →
build (Q-0172) over a marginal guard.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon runtime PR 1 — extract the `KnowledgeDomain` seam** | `needs-hermes-review` | The program's foundation: generalise the BTD6 stack's seam (data/fact-store/resolver/grounding) without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §3–4. |
| A2 | **Project Moon — first domain ingest (one game)** | `plan-first` | After the seam: a first Project Moon domain's data + vocabulary + grounding, the first usable increment. |
| B1 | **Creature-game — leaderboards UI + ranked** | `plan-first` | The #1244 provider exists; surface it (Explore-hub panel) + a ranked tier. Runtime, `needs-hermes-review`. |
| C1 | **botsite React-SPA migration** | `plan-first` | [plan](botsite-react-spa-migration-plan-2026-06-20.md) — migrate the live bot-site onto the design-system React app. |
| C2 | **Consistency-linter AI-nav PR 1** | `plan-first` | [plan](ai-panel-inplace-navigation-plan-2026-06-19.md); clears the `views/ai/` `edit_in_place` findings, then graduates the rule. Runtime/Q-0086, `needs-hermes-review`. |
| C3 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → `needs-hermes-review`. |
| D1 | **Reaction-roles PR 6 — PIL banner cards** | owner-paced | §4.6d; in flight as #1279 (`needs-hermes-review`) — needs Hermes/owner greenlight. |
| D2 | **Callout-trim actuator** (build the band-#1170 Q-0089 idea) | `ready` | Make the ▶ Next action prune deterministic — pairs with the line-budget guard. [idea](../ideas/reconcile-pass-tail-trim-actuator-2026-06-20.md). |
| E1 | **Mining grid-redesign follow-ups** | `plan-first` | The grid world (#1281/#1282) opened the hub-redesign plan's remaining slices. [plan](mining-hub-redesign-2026-06-15.md). |
| E2 | **Help-menu regrouping** | owner-directed | In flight as #1290 — logical re-sectioning so every feature is ≤3 clicks (simulation-driven). |
| E3 | **Pokétwo/MusicBot mapped features** | `plan-first` | From the #1180 feature-mapping plan, as the owner greenlights rows (music respects the #1185 legal findings). |

Gated/owner-paced (not in the buildable count): reaction-roles web builder (Surface A, control-API write +
security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision `botsite/` +
submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · AI-ticket build (Q-0183, own
session) · Explore-hub PR 2 + gated layers (Q-0182) · dashboard writes / control-API (security review) ·
Project Moon later phases (per-game data-sourcing, owner-paced).

## 5. The idea + the previous-pass review + the system improvement

**💡 New idea (Q-0089):** *reconcile-pass open-PR staleness classifier* — see
[`docs/ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md`](../ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md).
The Q-0125 open-PR disposition step is currently a manual read (`list_pull_requests` + eyeball each one's
age/label/CI). A small stdlib classifier could bucket open PRs into *active in-flight* (recent push, born-red
session in progress), *parked carve-out* (`needs-hermes-review`/`do-not-automerge`), and *genuinely stale*
(no push in N days, no carve-out label, CI red) — so the reconciler only has to *decide* on the stale bucket,
the one the routine warns is the easiest to miss (#766 sat red 21h).

**⟲ Previous-pass review (Q-0102):** the band-#1260 pass was thorough and its `trim_recently_shipped.py
--apply` + `band_pr_status.py --themes` tooling made *this* pass markedly faster — the grouped-entry
skeleton and the deterministic trim are exactly the kind of "leave the next run better-equipped" investment
the loop is for, and they paid off one band later. One small miss: its §4 listed **B1 Starboard PR 2** as a
fresh slice when #1259 (PR 1) was already in flight, so "builds on #1259" was the real framing — a reminder
to cross-check the in-flight set when writing the next-band queue, not just the merged ledger.

**🔧 System improvement:** the open-PR disposition step (Q-0125) is the one manual, judgment-heavy part of
the pass with no tooling assist — the idea above proposes the missing detector. It is the natural sibling of
the band-status classifier (#1181) and the trim actuator (#1206): the pass now has machine help for *ledger*
reconciliation but none for *open-PR* reconciliation, which is precisely where the documented misses (#766,
#771) happened.
