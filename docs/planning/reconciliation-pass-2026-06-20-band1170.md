# Reconciliation pass — 2026-06-20 · the band-#1170 Q-0107 cadence pass

> **Status:** `historical` — the docs-only review + planning pass for the band that crossed **#1170**
> (cadence = every **30th** merged PR per Q-0134; `#1170 = 30 × 39`; previous cadence pass
> [the band-#1140 pass](reconciliation-pass-2026-06-19-band1140.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1171**
> (`.github/workflows/reconciliation-trigger.yml`) — the **fourteenth** consecutive real cadence fire
> and live proof the loop self-fires: #1171 was authored by **`menno420`** (the `ROUTINE_PAT` owner),
> not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 the next band · §4 the
> idea→plan promotion this pass made · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#1170**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**Merged since the band-#1140 pass (band #1142–#1170):** the band's headline is the **federated
Explore-hub spine** shipping (PR 1 + PR 3) and the **public bot-site dark launch**, alongside a
workflow-hardening sweep (bug-book guards, instruction-core + arch/consistency guards) and the AI
self-introduction fix.

- **Federated Explore-hub spine (#1156 · #1158 · #1160).** Spine PR 1 (town-square world hub + world
  registry, re-parenting the #1131 mining Explore sub-hub), PR 3 (cross-game world card —
  `game_xp_service.world_identity()` + `views/explore/world_card.py` + `!worldcard`/`!mystats`), and the
  world-registry parity invariant + games-folio spine docs. **Spine PR 2 (global/per-game XP split) is
  reframed owner/runtime-gated** — a `player_skills` PK migration on a live progression table + an
  earning-model design call — so it is *not* an empty-fire lane (plan ⚠️ banner).
- **Public bot-site dark launch + botsite polish (#1147 · #1151 · #1152 · #1154 · #1168).** Stood the
  public bot site up dark on Railway, repointed the URL → `superbot-app.up.railway.app`, wired the "Add
  to Discord" install buttons (+ the #1154 dead-`/submit`-button Codex fix), and added the Claude Design
  React+Tailwind component library (`/design-sync`). Website v1 is code-complete; remainder is owner-paced
  rollout.
- **AI self-introduction advertises real capabilities (#1169).** A new always-assembled
  `_CAPABILITIES_OVERVIEW` system layer so the bot's self-intro names games / economy / progression, not
  just BTD6 (prompt discipline keeps BTD6 general so the faithfulness guard doesn't floor it).
- **Bug-book guards + BUG-0016/0018 root-fixes (#1143 · #1144 · #1146 · #1148 · #1157).** The
  deferred-root-fix backlog guard (#1144, Q-0172) + two review-hardenings, BUG-0018 (`site.json`
  hard-equality test no longer reddens on idea churn), BUG-0016 (single-source the reconcile-issue body).
- **Instruction-core + arch/consistency guards (#1162 · #1163 · #1166).** Pinned the always-loaded
  `.claude/` instruction core against pointer rot; extended the `baseview_inheritance` arch ratchet to the
  cog layer; pinned the `panel_base_class` allowlist to the conformance frozenset (parity test).
- **Ideas + journal captures (#1149 · #1150 · #1153 · #1159 · #1167)** and the **dashboard-refresh band**
  (#1145 · #1155 · #1161 · #1164 · #1165 · #1170, Q-0167 cadence regen).
- **#1142** — the previous band-#1140 reconciliation pass itself.

**Ledger reconciled:** `check_current_state_ledger --strict` flagged 23 merged PRs newer than the #1140
marker (benign-lag class). All of #1142–#1170 were absent from the live ledger; recorded as eight grouped
Recently-shipped entries, then trimmed the live list back to the 20 newest — moving the #1099-band, #1097,
the #1103-band, #1098, #1094, the #1081-band, #1064, and the #1065-band to `current-state-archive.md`.
`--strict` green afterward; `check_docs --strict` green.

**Control-plane reconciled (Q-0135):** `check_loop_health.py` reported SKIP (`gh` unavailable in-container
— the recurring mode), so the live read was done via the trigger-issue author — **#1171 authored by
`menno420`** confirms `ROUTINE_PAT` is set + the loop self-fires. Added #1171 to the canonical
control-plane table row 1 (`operations/autonomous-routines.md`) — fourteenth consecutive self-fire.

**Dashboard freshness:** `check_dashboard_data --drift` reported **OK ✓ (0 warnings, 45 cogs)** — no
structural identifier drift this band — and `export_dashboard_data.py` was re-run for cadence freshness.

### Open-PR disposition (Q-0125)

| PR | State | Disposition |
|---|---|---|
| #1074 (dependabot python-minor-patch dev group: ruff/pytest/pytest-xdist) | open | **Left** — routine dependabot dev-dep bump; merging needs the 3-place version sync (workflow / `requirements-dev.txt` / `.pre-commit-config.yaml`), a code change out of this docs-only pass's scope, and pytest 9.1.0 carries breaking changes worth a deliberate runtime session. Carried from the band-#1110/#1140 passes — still the only open PR; no red-CI orphan, no superseded `claude/*` PR. |

## 2. Band scorecard (vs. the band-#1140 next-band queue)

The band-#1140 queue ranked: (1) website P1–P8 wave, (2) federated Explore-hub PR 1, (3) consistency-linter
AI-nav PR 1, (4) procedures→skills batches, (5) Explore-hub PR 2/PR 3. **Strong consumption:** Explore-hub
**PR 1 + PR 3 shipped** (#1156/#1160), the website wave **completed to code-complete v1** (botsite dark
launch + polish #1147/#1151/#1152/#1154/#1168, on top of the prior band's #1109–#1123), and the AI-intro fix
(#1169) landed as a direct owner request. Not yet started: **consistency-linter AI-nav PR 1** (needs a
runtime/Q-0086 live-walk + `needs-hermes-review`) and **procedures→skills Batch 2** (edits CLAUDE.md →
`needs-hermes-review`). Explore-hub PR 2 was correctly reframed owner/runtime-gated rather than built blind.

## 3. The next band (depth to #1200)

#1200 is 30 merges out. **No PLAN-BACKLOG-THIN flag** — the buildable depth across existing plans + the
106-idea backlog is well over 30 PRs. **Honest caveat (unchanged from current-state):** the *cleanly-ungated
self-merge* subset is thin — the clean stdlib tooling/guard lanes are largely exhausted — so the next
dispatch should prefer a substantial `needs-hermes-review` lane or promote a fresh idea → plan → build
(Q-0172). This pass refreshes the ungated lane by promoting one idea (§4). Ranked:

1. **Consistency-linter rule 1 (`edit_in_place`) AI-nav redesign** —
   [plan](ai-panel-inplace-navigation-plan-2026-06-19.md) PR 1; clears the 17 `views/ai/` findings over a
   few PRs, then graduates `edit_in_place`. Runtime/Q-0086 live-walk, `needs-hermes-review`.
2. **procedures→skills remaining batches** ([plan](procedures-to-skills-conversion-plan-2026-06-17.md)) —
   Batch 2 (session enders → `/session-close`) edits CLAUDE.md → `needs-hermes-review`.
3. **`check_loop_health.py` gh-absent fallback** — promoted to a plan this pass (§4); ungated, refreshes the
   self-merge lane and makes the control-plane ROUTINE_PAT row script-verifiable.
4. **The cluster of ungated stdlib-guard quick-wins** (each disposable, Q-0105): `plan-homing-guard`,
   `band-pr-merge-status-helper`, `public-data-contract-field-snapshot`, `governance-files-presence-guard`.
5. **Owner-directed product ideas ready to promote** when the owner greenlights their gates:
   `per-command-feedback-threads`, `idea-to-cog-command-mapping`, the `cog-chooser-customize-before-invite`.

Gated/owner-paced (not in the buildable count): website rollout (provision `botsite/` + submissions DB,
domain cutover) · feedback-board PR 1 (owner dashboard auth) · the AI-ticket build (Q-0183, own session) ·
Explore-hub PR 2 + the gated layers (Q-0182) · dashboard writes / control-API (security review) · fishing
follow-ons (Q-0175) · BTD6 floors (exhausted).

## 4. The idea→plan promotion this pass made (Q-0172)

Promoted **[`loop-health-gh-unavailable-fallback`](../ideas/loop-health-gh-unavailable-fallback-2026-06-19.md)
→ a full executable plan**: [`planning/loop-health-gh-fallback-plan-2026-06-20.md`](loop-health-gh-fallback-plan-2026-06-20.md).
Rationale: it is the single highest-leverage *ungated* improvement available — it closes a gap **every
reconciliation pass hits**, including this one (`check_loop_health.py` SKIPs in-container because `gh` is
absent, so the control-plane ROUTINE_PAT row is only ever verified by a manual MCP read no checker can see).
The plan gives it a `gh`-absent fallback (GitHub REST over stdlib `urllib`, `GITHUB_TOKEN`-authenticated)
so the row becomes script-verifiable. Indexed in `docs/ideas/README.md` + `docs/roadmap.md`.

## 5. Pruned / fixed this pass

- Reset the `Last reconciliation pass` marker #1140 → **#1170**; next due at **#1200**.
- Added #1171 to the control-plane ROUTINE_PAT row (fourteenth consecutive self-fire).
- Trimmed the live Recently-shipped ledger to 20; updated the "Older merges (#1110 … #535)" pointer.
- Pruned the consumed band-#1140-fire owner-directive callout note status (left as the historical record).
- Regenerated `dashboard/data/dashboard.json` (cadence freshness; no structural drift).
- No new runtime bugs noticed (the band's BUG-0016/0018 were already fixed in it).

## 6. The system improvement this pass made

Two:

1. **Promoted the loop-health gh-fallback to a plan (§4)** — turning a recurring, self-inflicted
   verification gap into buildable work, the loop improving its own instrumentation.
2. **Filed a new Q-0089 idea** — [`recently-shipped-auto-trim-helper`](../ideas/recently-shipped-auto-trim-helper-2026-06-20.md):
   the Recently-shipped trim-to-archive step is the most mechanical and drift-prone part of every pass
   (count bullets · pick the oldest N · edit two files · hand-update the "Older merges (#X … #535)" floor
   pointer). A small stdlib actuator would make it deterministic, the natural complement to the existing
   `check_current_state_ledger.py` *detector*.

**⟲ Previous-pass review (Q-0102):** the band-#1140 pass was strong — planning-weighted per the owner's
directive, it routed four design questions and promoted two plans, and its next-band queue predicted this
band's actual work well (Explore-hub PR 1 + website wave both shipped as ranked). **What it (and every
prior pass) leaves growing:** the `current-state.md` ▶ Next action callout is now an enormous single
paragraph accreting consumed band-history across many bands — it fights its own "read THIS line" purpose.
The durable improvement: each pass should *aggressively* prune consumed band-history out of the live ▶ Next
action into its pass record (which already exists as the archive), keeping the callout to the live line + a
one-line pointer. This pass took a first cut; a dedicated trim is itself a good ungated session.
