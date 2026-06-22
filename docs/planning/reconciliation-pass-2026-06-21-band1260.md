# Reconciliation pass — 2026-06-21 · the band-#1260 Q-0107 cadence pass

> **Status:** `historical` — superseded by the [band-#1290 pass](reconciliation-pass-2026-06-22-band1290.md)
> (2026-06-22). The docs-only review + planning pass for the band that crossed **#1260**
> (cadence = every **30th** merged PR per Q-0134; `#1260 = 30 × 42`; previous cadence pass
> [the band-#1230 pass](reconciliation-pass-2026-06-21-band1230.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1264**
> (`.github/workflows/reconciliation-trigger.yml`) — the **seventeenth** consecutive real cadence fire
> and live proof the loop self-fires: #1264 was authored by **`menno420`** (the `ROUTINE_PAT` owner),
> not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed + control-plane
> · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker → **#1263**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**Merged since the band-#1230 pass (band #1234–#1263).** Two headlines: the **reaction-roles arc matured
well past the overhaul's PR 1–5** into Carl-bot-grade polish + self-heal, and a long **BTD6 data-lifecycle
session** added the buff-uptime model and closed the standing "owner must remember `seed-data`" manual step.
A **new Project Moon knowledge-domain program** was also stood up as design (Q-0192).

- **Reaction-roles arc — continuation / polish (#1234 · #1237 · #1242 · #1243 · #1245 · #1246 · #1248 ·
  #1250).** Multi-emote-per-message + menu reuse/repost (#1234); post-channel picker + auto-created
  colour/gradient roles (#1237); free temp-roles **member view** (#1242, `role_grants_cog`); message picker
  for the Add flow — no more copy-paste message ID (#1243); role presets + management-panel UX (#1245);
  gradient presets gallery (#1246); **dead-binding self-heal** — cleanup on role-delete + a panel hint
  (#1248) and auto-heal on the live reaction-listener path (#1250). The arc is now mature; only PR 6 (PIL
  banner cards) + the gated web builder remain ([plan](reaction-roles-overhaul-plan-2026-06-21.md)).
- **BTD6 buff-uptime + data auto-seed/drift (#1235 · #1249 · #1251 · #1255 · #1258 · #1263).** The
  **buff-uptime upgrade-detail** model — `btd6_upgrade_detail_service` + an AI tool + `parse_gamedata`
  extraction (#1235), data verify + populate (alchemist, #1249), **multi-target** uptime (#1251); then the
  **data-lifecycle hardening** — auto-seed BTD6 blob data on boot (`btd6_data_service` + env-var, #1255), a
  **content-drift surface** (#1258), and the `!btd6ops seed-data` **changed-report** (#1263). Closes the
  long-standing manual "run `seed-data` after deploy" owner step (now self-seeding + reporting drift).
- **Project Moon knowledge-domain program — design (#1238 · #1239 · #1240, Q-0192).** A NEW large program
  stood up as design: the **wiki-feasibility idea** ("can we serve a fandom wiki like BTD6 data?", #1238),
  the **full-parity program plan** (#1239 — owner picked full parity for all three games + lore, Q-0192),
  and the **pre-build recon** — data sources + the generalized `KnowledgeDomain` seam contract (#1240).
  Docs-only; the runtime build (extract the `KnowledgeDomain` seam from the BTD6 stack, then ingest) is the
  band's newest large buildable lane ([plan](project-moon-knowledge-domain-plan-2026-06-21.md)).
- **Creature leaderboard provider + Starboard plan (#1244 · #1254).** The creature-PvP **leaderboard rank
  provider** (`rank_providers`, #1244) feeding the shared ranking surface; and the **Starboard / Hall-of-Fame
  plan** (#1254, idea B1) — a reaction-triggered hall-of-fame reusing the reaction-listener seam. Its PR 1
  (#1259, migration 082) is in flight. [plan](starboard-plan-2026-06-21.md).
- **Workflow / docs (#1247 · #1253 · #1256).** **Q-0193 merge=deploy clarity** — Railway auto-redeploys
  `worker` on every merge to `main`, so a merged change is live within minutes; never tell the owner to
  "restart/deploy" a merge (CLAUDE.md + `production-deployment.md` + router, #1247); a journal capture of
  recurring **reaction-roles-chain workflow lessons** (#1253); a repo-state review + a `check_docs` guard
  hardening (#1256).
- **Dashboard generated-data refresh band (#1236 · #1241 · #1252).** The per-source-merge
  `dashboard-data-refresh` cadence regen of `dashboard/data/dashboard.json` (Q-0167).

**Ledger reconciled:** `check_current_state_ledger --strict` flagged 25 merged PRs newer than the #1231
marker (benign-lag class). All of #1234–#1263 were absent from the live ledger; recorded as six grouped
Recently-shipped entries, then ran `trim_recently_shipped.py --apply` to move the 6 oldest bands
(#1186 · #1156-band · #1147-band · #1143-band · #1162-band · #1149-band) to `current-state-archive.md` and
recompute the floor pointer. `--strict` green afterward (27 PRs present); `check_docs --strict` green.

**Control-plane reconciled (Q-0135):** `check_loop_health.py` reported SKIP (`gh`/`GITHUB_TOKEN`
unavailable in-container), so the live read was done via the trigger-issue author — **#1264 authored by
`menno420`** confirms `ROUTINE_PAT` is set + the loop self-fires. Added #1264 to the canonical control-plane
table row 1 (`operations/autonomous-routines.md`) — seventeenth consecutive self-fire.

**Dashboard freshness:** re-ran `export_dashboard_data.py` for cadence freshness; it had drifted (ideas 114,
updates 60, bugs 23, commands 316) and was regenerated for `dashboard.json` + `site.json` + `data.js`.
`check_dashboard_data --drift` reported clean (48 cogs validated) afterward.

### Open-PR disposition (Q-0125)

| PR | State | Disposition |
|---|---|---|
| #1259 (Starboard / Hall-of-Fame PR 1 — migration 082 + service + cog) | open | **Left** — a **live in-flight session** (born-red card `in-progress`, created 21:16Z, ~30 min before the reconcile issue), executing the #1254 Starboard plan. Runtime `disbot/`; not stale/redundant/mine. |
| #1260 (git-based PR-mergeability check tooling) | open | **Left** — in-flight born-red tooling session (created 21:27Z), diagnoses the GitHub `mergeable_state: dirty` false-report; not docs-only-reconcilable. |
| #1262 (Creature-PvP 🔄 Rematch button — self-initiated) | open | **Left** — in-flight born-red session (created 21:43Z), a small self-initiated UX slice on the creature-PvP outcome embed. |
| #1261 (dashboard-data-refresh — automated) | open | **Left** — the `dashboard-data-refresh` workflow's own bot PR; auto-merges on green. |

No stale, red-stuck, or redundant `claude/*` PRs were open this pass — all four open PRs were created within
~35 min of the reconcile issue and are active in-flight or automated. Cleanest disposition since band-#870.

## 2. Band scorecard (vs. the band-#1230 next-band queue)

The band-#1230 §4 queue ranked: A1 creature PvP user-facing flow (in flight #1230), A2 creature leaderboards,
A3 result persistence/ranked, B1 botsite React migration, C1 consistency-linter AI-nav PR 1, C2
procedures→skills Batch 2, D1 reaction-roles PR 6, D2 callout-trim actuator, E1 Pokétwo/MusicBot features.
**Consumption:** **A1 landed** (#1230 merged out-of-band; its result-recording + leaderboard #1257 also
landed), **A2 partially shipped** (#1244 leaderboard rank provider). **Off-queue but dominant — and healthy:**
the band's two headlines (the reaction-roles maturation arc and the BTD6 data-lifecycle session) were
owner-/dispatch-driven, not on the ranked queue, plus a **whole new owner-directed program** (Project Moon,
Q-0192) was stood up. As in the prior two bands, the owner drives product while the ranked queue tracks the
*autonomous* backlog — the big self-merge lanes (B1 botsite, C1 AI-nav, C2 procedures→skills) remain unstarted
because they want runtime / CLAUDE.md-editing sessions.

## 3. Pruned / fixed this pass + control-plane

- Reset the `Last reconciliation pass` marker #1231 → **#1263**; next due once merges cross **#1290**
  (`1263 // 30 == 42`, so no re-fire until band 43).
- Added #1264 to the control-plane ROUTINE_PAT row (seventeenth consecutive self-fire).
- **Kept the ▶ Next action callout lean (Q-0102 standing prune).** It was already trimmed to ~3.8 KB by the
  eighteenth pass; this pass rewrote it fresh for band-#1260 at a similar size (well under the 6 KB budget the
  band-#1230 line-budget-guard idea proposed), pointing history to the per-band records.
- Re-badged the band-#1230 pass record `plan` → `historical` (its callout + Recently-shipped links rotated
  out this pass — the same `test_check_plan_homing.py` exemption the eighteenth pass documented).
- Regenerated `dashboard/data/dashboard.json` + `botsite/data/site.json` + `data.js` (cadence freshness;
  they had structurally drifted).
- **Runtime bugs noticed this pass:** none new (docs-only pass; BUG-0019 #1 stays the open owner-design fork,
  BUG-0011 stays the open Hermes-infra item — both pre-existing).

## 4. The next band (depth to #1290)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** The
band added a **multi-PR program** (Project Moon, Q-0192) on top of the existing deep lanes (Starboard PR 2,
botsite React, AI-nav, procedures→skills, creature leaderboards/ranked). **Honest caveat (carried,
unchanged):** the *cleanly-ungated self-merge* subset is thinner than the headline count — Project Moon's
runtime build and the AI-nav / procedures→skills batches are runtime / `needs-hermes-review`, so an empty
*autonomous* fire should prefer a substantial review-gated lane or promote a fresh idea → plan → build
(Q-0172) over a marginal guard.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon runtime PR 1 — extract the `KnowledgeDomain` seam** | `needs-hermes-review` | The program's foundation: generalise the BTD6 stack's seam (data/fact-store/resolver/grounding) without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §3–4. |
| A2 | **Project Moon — first domain ingest (one game)** | `plan-first` | After the seam: a first Project Moon domain's data + vocabulary + grounding, the first usable increment. |
| B1 | **Starboard PR 2 — config panel + polish** | `plan-first` | `BaseView` admin-hub config panel · self-star exclusion · ignore-channels · optional XP bonus. Builds on #1259. [plan](starboard-plan-2026-06-21.md) §6. |
| B2 | **Creature-game — leaderboards UI + ranked** | `plan-first` | The #1244 provider exists; surface it (Explore-hub panel) + a ranked tier. Runtime, `needs-hermes-review`. |
| C1 | **botsite React-SPA migration** | `plan-first` | [plan](botsite-react-spa-migration-plan-2026-06-20.md) — migrate the live bot-site onto the design-system React app. |
| C2 | **Consistency-linter AI-nav PR 1** | `plan-first` | [plan](ai-panel-inplace-navigation-plan-2026-06-19.md); clears the `views/ai/` `edit_in_place` findings, then graduates the rule. Runtime/Q-0086, `needs-hermes-review`. |
| C3 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → `needs-hermes-review`. |
| D1 | **Reaction-roles PR 6 — PIL banner cards** | owner-paced | §4.6d; deliberately deferred, owner-paced. |
| D2 | **Callout-trim actuator** (build the band-#1170 Q-0089 idea) | `ready` | Make the ▶ Next action prune deterministic — pairs with the line-budget guard. [idea](../ideas/reconcile-pass-tail-trim-actuator-2026-06-20.md). |
| E1 | **Pokétwo/MusicBot mapped features** | `plan-first` | From the #1180 feature-mapping plan, as the owner greenlights rows (music respects the #1185 legal findings). |

Gated/owner-paced (not in the buildable count): reaction-roles web builder (Surface A, control-API write +
security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision `botsite/` +
submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · AI-ticket build (Q-0183, own
session) · Explore-hub PR 2 + gated layers (Q-0182) · dashboard writes / control-API (security review) ·
Project Moon later phases (per-game data-sourcing, owner-paced).

## 5. The idea + the previous-pass review + the system improvement

**The Q-0089 idea this pass added:**
[`band-pr-status-author-classifier`](../ideas/band-pr-status-author-classifier-2026-06-21.md) — every
reconciliation pass spends real effort hand-theming the band's merge-commit PRs (peaceful-mayer, ecstatic-babbage,
funny-franklin branches whose merge titles say nothing) by running `git show --stat` per PR to read the file
fan-out. `band_pr_status.py` already classifies merged/open, but **not theme**. The idea: a small `--themes`
mode (or a sibling) that groups a band's merged PRs by their **touched top-level path prefix** (`disbot/cogs/`,
`disbot/services/btd6_*`, `docs/planning/`, `dashboard/`) and the squash-title verb, emitting a *draft*
grouped-entry skeleton the pass can edit rather than reconstruct cold — turning the most manual half of every
pass (figuring out *what* the opaque merge-commit PRs did) into a one-command starting point.

**⟲ Previous-pass review (Q-0102):** the band-#1230 pass was strong — it **did** the long-deferred ▶ Next
action prune *in-band* instead of routing it to a hypothetical future session (correctly diagnosing that "a
cleanup always one session away is never done"), and filed the line-budget-guard idea so the next agent gets a
number not a vibe. **Where it could improve, and this pass acted on it:** that pass's open-PR disposition
table had exactly one row (#1230) and read cleanly, but it relied entirely on the *author/timestamp* heuristic
("opened the same minute as the reconcile issue") to call a PR in-flight — which is correct but **undocumented
as a rule**. This pass made the heuristic explicit in every disposition row (created-time vs. the reconcile
issue time, born-red card state) so a future pass disposing a *genuinely* stale PR can tell it apart from an
active one by the same recorded signal. **The durable improvement (initiated, not waited-for):** the Q-0089
idea above attacks the single most time-consuming part of the pass — the band-PR theming — which is the natural
next lever now that the *trim* (band-#1170 idea, #1181) and the *callout prune* (band-#1230, done in-band) are
both solved. The reconciliation routine is steadily mechanising itself one chore at a time; the band-theming
classifier is the next chore in line.
