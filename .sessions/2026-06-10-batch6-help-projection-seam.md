# 2026-06-10 — Batch 6: Help projection seam (HLP-2) + Q-0074 admin-tier fix

PR **#657** (draft at first push per Q-0052; marked ready at session end).
Executed consolidated-plan **Batch 6** — the Help projection seam — on the #642
characterization net, per the help audit §9 contract + §11 internal order
(projection contract → catalogue → read model → renderers).

## Arc

1. **Route:** current-state ▶ → consolidated plan Batch 6 → help audit §9/§11
   (grep-headers-first) → source (help_cog/route/access_projection/registries/
   #642 net/Batch-5 access_map patterns). Context maps run before every
   `disbot/` edit.
2. **Services first, tests first.** `services/help_catalogue.py` (stable-keyed
   hub/subsystem inventory; four drift-finding kinds — `hub_without_subsystem`/
   `unknown_parent_hub`/`tier_mismatch`/`roster_drift` — pinned **empty**) and
   `services/help_projection.py` (audit-§9 vocabulary exactly; only
   `display_hidden`/`governance_hidden` hide; `from_visibility` sync hot path;
   `registry_defaults` pinned byte-equivalent to legacy `hubs_for_tier`;
   `project_help_with_execution` composes `access_projection` for the
   non-hiding lock states). 26 contract tests green before any renderer moved.
3. **Q-0074 rode along** (the answer's named destination): `admin`
   `visibility_tier` owner → administrator (inventory: `!adminmenu`/stats are
   administrator routes; cog load/unload/reload + sync keep `is_owner()`).
   Without it, Home-consumes-governance would have *hidden the Admin hub from
   administrators* — the audit's flagged tier mismatch, now structurally pinned
   by the catalogue finding.
4. **Renderer flip** — all five paths consume one `HelpProjection`:
   Home (host-subsystem governance awareness), Advanced (same output, single
   source), typed/dropdown hub+subsystem routes (hidden target ⇒ not-found,
   no leak), single-command route (shared display filter), dedicated-panel
   dispatch + `HelpPanelView._on_select` click-time re-check. Deleted
   production-dead `build_overview_embed` (795-LOC cog needed headroom).
5. **Conscious pin flips:** 10 test files updated with `HLP-2:` markers; the
   #642 net extended with a 6-test per-path unification section (29 total).
6. **Verify:** CI mirror **8,621 passed** · arch **0 errors** (87→86 warnings)
   · `check_docs` ✓ · live smoke (fresh DB boot, 0 error lines, HelpCog loads;
   live render: catalogue 10/29/**0 findings**, user Home unchanged, admin
   Home all 10 hubs, enriched projection over the live access map).

## Decisions made alone (flagging for review)

- **Hidden target ⇒ not-found copy identical to nonexistent** (no
  "exists but hidden" leak). Felt forced by governance-hiding semantics.
- **Lock states never hide** — `routed_off`/`command_locked` stay advertised;
  rendering a 🔒 badge is overlay/preview territory, not this batch. Matches
  `help_advertises_locked` ownership (P1B) and HLP-4.
- **`open_route` signature break** (`visible_subsystems`/`member_tier` →
  `projection=`) vs builders keeping a `member_tier` *fallback* that builds
  `registry_defaults` (restore symmetry + low test churn). One decision path
  either way; the fallback is pinned equivalent.
- **Single-command help now hides disabled commands** (`cmd.enabled=False`) —
  unification with the list filter; could surprise a dynamic-disable flow.

## Context delta (reflection interview)

- **Route miss:** none material — the consolidated plan's Batch 6 block +
  audit §9/§11 + the #642 net were exactly sufficient. The orientation chain
  (current-state ▶ → plan → audit § route) worked as designed.
- **Route excess:** reading audit §2–§8 in full was ~40% skimmable; §3's
  "Visibility and authorization actually applied" table + §9 + §11 carried
  the whole design. The §9-route line in the plan could say "the §3 table is
  the divergence spec".
- **Discovered by hand:** (1) the Q-0074 ⇄ Batch-6 coupling — Home consuming
  governance *regresses the Admin hub for admins* unless the registry fix
  lands first; neither the plan's Batch 6 block nor router §31 cross-linked
  them (now recorded in both). (2) `_build_page_embed`'s `member_tier` param
  is dead. (3) MagicMock commands are truthy-`hidden` under any real display
  filter — two test files relied on the old no-filter behavior.
- **Weak point of what shipped:** dedicated panels consume the projection
  only at *dispatch*; panel-internal rosters (e.g. a hub view listing its
  children) still filter however each builder chooses — that's the audit's
  staged Phase 4/7 territory, not silently claimed here. And the projection
  is uncached per render (3 accessor scans over ~40 decisions — fine; a
  cache needs an invalidation owner per §16.6 discipline).
- **One change that would have helped:** the plan batch listing its *known
  decision couplings* (here: Q-0074) the way it lists files/tests/stop
  conditions.

## Pointers

- Outcome record: consolidated plan §5 Batch 6 note + §6 HLP rows;
  audit §11 banner; ownership.md services row; surface-map routing bullet.
- Next in lane: **HLP-3 overlay** (Q-0055–Q-0059 answered) once #657 is
  merged + smoked; then audit finding-4 metadata moves (Home copy / alias
  tables → catalogue).
