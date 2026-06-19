# Reconciliation pass — 2026-06-18 · the band-#1050 Q-0107 cadence pass

> **Status:** `historical` — the docs-only review + planning pass for the band that crossed **#1050**
> **Superseded 2026-06-19 (was active):** Superseded by band-#1080 → band-#1110 (the live next-band queue). Do not act on this — current map: [planning/README](README.md).
> (cadence = every **30th** merged PR per Q-0134; previous cadence pass
> [the band-#1020 pass](reconciliation-pass-2026-06-17-band1020.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1051**
> (`.github/workflows/reconciliation-trigger.yml`) — the **tenth** consecutive real cadence fire of
> the autonomous issue-trigger, and live proof the loop self-fires: #1051 was authored by
> **`menno420`** (the `ROUTINE_PAT` owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 priorities restated ·
> §4 the next band · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#1050** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#1020 pass (band #1021–#1050):** a fast, broad band. Three threads dominated:

- **The repo-consistency-linter (Q-0170) — the flagship ungated lane.** From the harness + rule 1
  (#1042) through rules 2/3 (#1043), rule 4 select-truncation (#1044), the shared
  `views/paginated_select.py` `PaginatedSelectView` primitive + 53→31 truncation triage (#1047), the
  standalone-picker migrations (#1048), and the embedded `attach_windowed_select` helper + 28→15 triage
  (#1050). This lane fixed real >25-option silent-drop bugs (the #1040 class) and ratcheted the
  `baseview_inheritance` arch debt 12→9 along the way.
- **Fishing v1 — built then reconciled to the owner's #1036 spec (Q-0175).** The interim #1033 build
  (14 fish, coins) was reconciled to the 21-fish / level×size-band / no-coins spec in #1039 + #1041.
  Now **owner-design-gated** (loadout presets · value/cook/sell · catch minigame are deferred open
  questions per Q-0175).
- **BTD6 deterministic-floor lane — now exhausted.** #1023 (moderation DM, the band-#1020 §4 slice),
  #1024 (paragon-ability + boss tier-HP floors), #1035/#1037/#1038 (owner live-test answer fixes).
  All towers/heroes/paragons/bosses/MK/relics/bloons roster+comparison shapes are covered.

Plus workflow/ops: #1022 (the band-#1020 reconcile pass itself), #1026 (autonomous-routines review +
`dashboard-data-refresh` workflow), #1027 (generated-artifact freshness umbrella), #1028
(procedures→skills conversion plan), #1029 (**idea→plan gate opened, Q-0172**), #1030 (Hermes
plain-language house style), #1031 (local character-render preview tool), #1032/#1034 (Q-0173/Q-0174
Codex integration + decisions), #1036 (fishing open-world expansion plan), and the dashboard plumbing
PRs (#1045 CI fix, #1046/#1049 generated-data refresh).

**Ledger reconciled:** at pass start, `check_current_state_ledger --strict` reported green (it checks
only the last 15), but a per-PR grep of the #1021–#1050 band found **two genuinely-missing** entries —
**#1022** (the band-#1020 reconcile pass) and **#1029** (the idea→plan gate, Q-0172). Both were merged
yet never recorded. Added both, then trimmed the live Recently-shipped list back to the 20 newest
(it had grown to 41, 21 over the ratchet), moving #1026 … #975 to `current-state-archive.md`. This is
the same false-green class the CLAUDE.md § "green check that contradicts visible evidence" warns about:
the strict checker's 15-PR window can't see drift older than its window but newer than the marker.

**Open-PR disposition (Q-0125):** `list_pull_requests` (state=open) returned **zero open PRs** — the
cleanest disposition state. Nothing to close, fix, or flag.

**Carve-out merge catch (Codex review on this pass's PR #1053):** the per-PR sweep also surfaced that
the two long-carried `needs-hermes-review` carve-outs — **image-mod #941** (merged 04:24) and
**security tiers 1+2 #929** (merged 04:17) — **both landed 2026-06-18**, yet the prior passes' prose
(and this pass's first draft) still listed them as open gates. Recorded them as shipped (a grouped
archive entry) and corrected §2/§3/§4/§6 + the live ▶ Next action to drop them as open gates / spent
the "merge the two PRs" owner-lever. Verified against `git log origin/main` (Codex is input to verify,
not an order — Q-0120; here it was correct).

**Control-plane (Q-0135):** `check_loop_health.py` returned **SKIP** (`gh` unavailable in this
container). Did the live read via the GitHub MCP instead: reconcile issue **#1051** is authored by
**`menno420`** (a real-user login), which is the live proof `ROUTINE_PAT` is set and the loop
self-fires — appended #1051 to the row-1 re-confirmation list in the Control-plane state table. Rows
2/6 stay verified; rows 3–5 remain maintainer-side (not repo-verifiable).

## 2. Band scorecard — band-#1020 §4 queue vs. what shipped

| Planned slot (band-#1020 §4) | Outcome |
|---|---|
| 2 · Moderation-DM config (`ready`) | ✅ **#1023** |
| 3 · Dashboard manifest spine PR4 (`owner`/`creds`) | ⬜ owner-paced (write side) — not started |
| 4 · AI §7 next workflow family (`plan-first`) | ⬜ deterministic floors exhausted; no new family planned this band |
| 5 · Image moderation #941 lands (`owner`/review) | ✅ **MERGED #941** (2026-06-18 04:24) — the `needs-hermes-review` carve-out landed |
| 6 · Security tiers 1+2 #929 lands (`owner`/review) | ✅ **MERGED #929** (2026-06-18 04:17) — the `needs-hermes-review` carve-out landed |
| 7 · Hermes bug-triage `gh issue create` write (`plan-first`) | ⬜ not started |
| 8 · P1-1 absence-guard Layer B (`creds`) | ⬜ still creds/design-gated |
| 9 · BUG-0009 newest-towers ordering (`data`) | ⬜ still data-gated |
| 10 · Buffer / steered | ✅ **the consistency-linter lane became the band** (#1042–#1050) + the BTD6 live-test fixes (#1035/#1037/#1038) + fishing reconcile (#1033/#1039/#1041) |

**Read:** as in the last several bands, the *planned* product slots were mostly gated (owner/creds/
review/data), and the **buffer became the band** — this time the owner-directed consistency-linter
(Q-0170) plus owner live-test bug fixes. The one planned `ready` slot (moderation DM) shipped. The
recurring pattern is now structural, not incidental (see §3).

## 3. Priorities restated — the product/tooling asymmetry (the honest read)

The **bot-product sectors (S1 bot / S2 BTD6) are gated or exhausted**: the BTD6 deterministic-floor
lane is complete; fishing is owner-design-gated (Q-0175); absence-guard Layer B is creds-gated;
newest-towers is data-gated; the dashboard write/manifest lanes are owner-paced. **This is not a
backlog failure — it is the correct gate state.** Those lanes genuinely need an owner decision, prod
creds, or sourced data before more code is right. *(The two `needs-hermes-review` carve-outs that the
prior several passes carried as open — image-mod #941 + security tiers #929 — **both MERGED
2026-06-18**, so that lever is now spent; this pass corrected the ledger + ▶ Next action to record
their shipped state.)*

The **workflow/tooling sectors (S3 AI-Memory / S4 docs / S5 ops) are deep and ungated** — and that is
where the next band's buildable work lives. The flagship is the consistency-linter migration; behind
it sit two real multi-PR plans (procedures→skills, owner-review-inbox Phase 1) and a rich shortlist of
small stdlib guards. So the band is **fillable, but it will be tooling/workflow-heavy** rather than
bot-feature-heavy. That asymmetry is worth the owner seeing: *if you want the next band to ship more
bot features, the highest-leverage owner action is to unblock a gated product lane* — decide the
fishing Phase-1 open questions (Q-0175) or greenlight a dashboard write surface. (The merge-the-two-
`needs-hermes-review`-PRs lever is now spent — #941 + #929 both landed 2026-06-18.) Absent that, the
agents will (correctly) build workflow/tooling depth.

## 4. The next band — buildable, highest-value first

> Gate-state tags: `ready` · `creds` · `owner` · `plan-first` · `data`. The `#` column is **slot
> sequence, NOT reserved PR numbers** (GitHub assigns numbers globally — Q-0142). Pick the next slice
> by its **description**, verified against the live ledger. Owner steers override freely. This band is
> deliberately tooling/workflow-weighted (§3) — every slot below is a real, ungated slice unless tagged.

**Lane A — consistency-linter (the flagship, Q-0170, all `ready`):**

| # | Slice | Scope anchor |
|---|---|---|
| A1 | **Migrate the `views/selectors/` API-ripple set onto `attach_windowed_select`** (role/channel/multi/multi_role/subsystem — `discord.ui.Select` subclasses added via `add_item`; convert each to an `attach_*` helper + update its ~8 consumers) — one focused PR | [repo-consistency-linter-plan](repo-consistency-linter-plan-2026-06-17.md) · `views/paginated_select.py` |
| A2 | **Migrate the per-panel embedded selects** (`channels/move_panel`·`visibility_panel`·`create_panel`, `settings/subsystem_view` edit/reset, `setup/sections/channels`, `access/explorer`, `diagnostic/automation_panel`) — small per-panel swaps now the helper exists; pass `select_row`/`nav_row` per the `access_map` pattern | same |
| A3 | **Rule graduation (b):** once a rule runs quiet on a clean tree across a few sessions, flip it error + wire into `code-quality.yml` | same |
| A4 | **Extend rule 4 (select-option truncation) to `disbot/cogs/`** | same |

**Lane B — workflow/tooling plans (ungated multi-PR initiatives):**

| # | Slice | Gate | Scope anchor |
|---|---|---|---|
| B1 | **Procedures→skills conversion — Batch 1** (the C-bucket-safe relocations; thin-pointer convention; born-red for the CLAUDE.md edit) | `ready` | [procedures-to-skills-conversion-plan](procedures-to-skills-conversion-plan-2026-06-17.md) |
| B2 | **Procedures→skills — Batches 2–4** (one PR each, per the build-order table; Codex feedback folded) | `ready` | same |
| B3 | **Owner-review-inbox — Phase 1** (read-only "Review board" page + a `reviews` block in the dashboard export; zero owner setup) | `ready` | [owner-review-inbox-plan](owner-review-inbox-plan-2026-06-17.md) |

**Lane C — small stdlib guards (ungated, one PR each, `ready`, Q-0105 disposable tooling):**

| # | Slice | Scope anchor |
|---|---|---|
| C1 | **`check_plan_backlog.py`** — automate the Q-0164 PLAN-BACKLOG-THIN flag (count buildable `ready` slices vs. the cadence) | [agent-tooling-automation-shortlist](../ideas/agent-tooling-automation-shortlist-2026-06-17.md) |
| C2 | **`check_routine_permission_surface.py`** — fail when any routine command resolves to `ask` in `.claude/settings.json` | [routine-permission-surface-lint](../ideas/routine-permission-surface-lint-2026-06-16.md) |
| C3 | **`check_ledger_hygiene.py`** — flag duplicate claim branches / idea-file links in the `merge=union` ledgers | [ledger-dedup-linter](../ideas/ledger-dedup-linter-2026-06-16.md) |
| C4 | **`scripts/_docs_ledger.py`** — extract the repeated markdown-ledger regexes (Status/`BUG-NNNN`/idea-file) into one shared module | [docs-ledger-parsing-helper](../ideas/docs-ledger-parsing-helper-2026-06-16.md) |
| C5 | **Cog `SUBSYSTEM` self-declaration** — replace the name-guess + three drift-prone lists with an authoritative cog attribute the scanner reads | [cog-declares-its-subsystem](../ideas/cog-declares-its-subsystem-2026-06-16.md) |

**Lane D — the agent-tooling skills shortlist (`plan-first` → then `ready`):** `/route-idea`,
`/cog-review`, `/plan-band`, `/fix-drift` Claude Code skills
([shortlist](../ideas/agent-tooling-automation-shortlist-2026-06-17.md)) — promote each to a complete
skill spec, then build (the idea→plan gate Q-0172 lets a session do both).

**Gated / owner-action (not in this band unless the owner steers — see §3):** fishing Phase-1 open
questions (Q-0175 — owner decides) · dashboard manifest PR4 write side (owner-paced) · absence-guard
Layer B (creds) · BUG-0009 newest-towers (data) · the substrate-kit (owner-action since band-#900).
*(Image-mod #941 + security tiers #929 are no longer here — both MERGED 2026-06-18.)*

**Depth check (Q-0164):** Lanes A–D total **~18–22 genuine `ready`/`plan-first` slices** — enough
buildable work to reach the next cadence pass without inventing filler. **No `⚠️ PLAN BACKLOG THIN`
flag this pass** — the queue is deep on the workflow/tooling side. The honest caveat (§3) is that it is
*workflow-weighted*; the lever to rebalance toward bot features is owner-side (unblock a gated lane).

## 5. Pruned / fixed by this pass

- **Ledger:** added the missing **#1022** + **#1029** entries; trimmed Recently-shipped 41→20 (moved
  #1026 … #975 to the archive); rewrote the "Older merges" pointer line to record this pass's trim.
- **Control-plane:** appended reconcile issue **#1051** to the row-1 `ROUTINE_PAT` re-confirmation list.
- **Dashboard export:** regenerated `dashboard/data/dashboard.json` (cadence freshness, Q-0167).
- **Marker:** reset `Last reconciliation pass` #1020 → **#1050**.

## 6. The system improvement this pass made

**Named the product/tooling asymmetry as a standing, structural condition (not band noise) — and gave
the owner the lever.** For ~6 consecutive bands the *planned product slots* have been mostly gated and
the *buffer (workflow/tooling)* has become the band. This pass stops treating that as a per-band
surprise and writes it into §3 as the steady state, with the explicit owner-side lever: the fastest way
to make a band ship more bot features is to unblock one gated product lane (decide Q-0175 fishing or
greenlight a dashboard write surface — the merge-the-two-`needs-hermes-review`-PRs lever was spent when
#941 + #929 landed 2026-06-18). This turns a
recurring observation into an actionable owner signal — the same spirit as the Q-0164 PLAN-BACKLOG-THIN
flag, but for the *product-vs-tooling balance* rather than raw depth.
