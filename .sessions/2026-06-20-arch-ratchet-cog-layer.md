# 2026-06-20 — Extend the `baseview_inheritance` arch ratchet to the cog layer

> **Status:** `complete`

## Arc

Scheduled dispatch fire, no work order → advance the next ungated plan slice. Picked the
candidate current-state ▶ Next action named explicitly: *"extend the `views/`-scoped
`baseview_inheritance` arch conformance ratchet to the cog layer too, so the arch checker —
not just the consistency linter — tracks cog-layer direct-View classes."* Turned out to also
be the concrete-gap half of a captured idea (`ideas/cogs-layer-view-residence-guard-2026-06-14.md`).

## Shipped (PR #1163)

- **`scripts/check_architecture.py` `check_baseview_inheritance`** now scans both `views/`
  **and** `cogs/` (was `views/`-only). `cogs/` was a documented blind spot — the ratchet
  test comment itself said "cogs/ are not scanned by this ratchet" — so a cog-layer
  `discord.ui.View` panel passed the **load-bearing arch CI gate** silently. (The warn-only
  consistency linter rule 3 `panel_base_class` already covered cogs since #1128; this brings
  the arch checker — the harder gate — to parity.)
- **`tests/unit/views/test_view_base_class_conformance.py`** — pinned the 5 existing
  cog-layer direct-`discord.ui.View` classes into the conformance frozenset
  (`deathmatch_cog._DuelView`/`_ChallengeView`, `logging/provision_view.LogChannelProvisionView`,
  `logging/select_view.LogChannelSelectView`, `settings_cog._DisabledHelpHookView`), with the
  reasons mirrored from `architecture_rules/consistency_exceptions.yml` (#1128's triage). A new
  cog-layer direct-View class now **fails the ratchet**. De-staled the docstring + the now-false
  "cogs/ are not scanned" comment.
- **Groomed the idea** `cogs-layer-view-residence-guard-2026-06-14.md`: direct-View half DONE;
  the broader *residence* guard (no view/modal class defined in `cogs/` at all) inventoried —
  **38** view-like classes currently live under `cogs/`, most correctly extending
  `HubView`/`PersistentView`/`BaseView`/`Modal`. Declaring all 38 "must move to `views/`" is a
  cross-cutting architectural stance → **routed for an owner decision**, not built unilaterally.
- Drift-on-sight (Q-0166): pruned the stale merged `funny-franklin-2d6daf` (#1162) claim line
  from `docs/owner/active-work.md`.

Verification: `check_quality.py --full` green; `check_architecture.py --mode strict` clean
(baseview entries are warn-level by design, the test is the ratchet); `check_docs.py --strict`
green; conformance test passes.

## Context delta

- **Needed but not pointed to:** nothing new — current-state ▶ Next action named this exact
  candidate, and `ideas/cogs-layer-view-residence-guard-2026-06-14.md` pre-described the gap.
  The orientation route worked well here.
- **Pointed to but didn't need:** the giant current-state ▶ Next-action paragraph is now so
  long that locating the *live* sentence costs real effort (it took a `grep -o` to find the
  handoff phrase). Not a miss — a scaling smell (see Q-0102 review below).
- **Discovered by hand:** that the consistency linter (rule 3, #1128) and the arch ratchet
  (`baseview_inheritance`) are two *separate* enforcers of overlapping ground truth — the
  linter covers `views/`+`cogs/`, the arch ratchet covered only `views/`. They can drift; this
  run closed the cog gap but they remain two allowlists to keep in step.

## Decisions made alone

- Pinned the 5 cog-layer direct-View classes (rather than migrating them to BaseView) — they
  are already documented specialized-lifecycle exceptions in `consistency_exceptions.yml`;
  mirroring that decision keeps one source of truth. Reversible (the frozenset only shrinks).

## Flagged for maintainer

- **Owner decision routed:** is *"Discord view/modal classes must be defined under `views/`,
  never inline in `cogs/`"* a rule worth a 38-class warn-then-ratchet residence guard? Many of
  the 38 are a cog's own hub panel where `views/` residence is a judgment call, not an obvious
  win. Captured in the idea doc's ▶ Update. Until decided, the *direct-View* half (this PR) is
  the enforced subset.

## 💡 Session idea (Q-0089)

**A `consistency_exceptions.yml`-vs-arch-frozenset cross-allowlist drift guard.** This run
surfaced that the `panel_base_class` consistency-linter allowlist and the arch ratchet's
`_KNOWN_DIRECT_VIEW_SUBCLASSES` frozenset both enumerate the *same* documented direct-View
exceptions, maintained by hand in two files. A small stdlib test asserting the two sets agree
(modulo the views/games/ai path exemptions) would stop them silently diverging — when one is
ratcheted down and the other isn't, the "two sources of truth" smell I hit this run becomes a
real drift. Genuinely worth having; lane = tooling/consistency. (Not built this run — flagged
to keep the PR single-purpose; a clean grooming-lane candidate.)

## ⟲ Previous-session review (Q-0102)

The previous dispatch run (`funny-franklin-2d6daf`, #1162) extended `check_docs.py`'s pinned
check to the `.claude/` instruction core + routine prompts — a genuinely good stale-pointer
guard for the thin-pointer convention, and it fixed a pointer it surfaced. **What it missed:**
it left its `active-work.md` claim line behind (I pruned it this run) — the session-close
"remove your claim" step is easy to forget and nothing enforces it. **System improvement it
surfaces:** the current-state ▶ Next action single paragraph has grown to ~30KB on one logical
line; the *live* sentence is now genuinely hard to find inside the historical band-snapshots
appended after it. The convention "trust THIS sentence, never a lower ▶" is holding, but the
ergonomics are degrading — a future reconciliation pass should consider *physically truncating*
the historical tail into the band pass-record docs it already links, leaving ▶ Next action as
just the live queue. (Captured as an observation, not built — it's a reconciliation-routine call.)

## 📤 Run report

- **Did:** extended the `baseview_inheritance` arch ratchet to scan `cogs/`, pinning the 5
  existing cog-layer direct-View classes · **Outcome:** shipped
- **Shipped:** #1163 — arch checker now tracks cog-layer direct-`discord.ui.View` panels (was a
  `views/`-only blind spot); closes the direct-View half of the cogs-layer-view-residence idea
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** is "view/modal classes must live under `views/`, never inline in
  `cogs/`" a rule worth a 38-class residence ratchet? (the residence half of
  `ideas/cogs-layer-view-residence-guard-2026-06-14.md` — routed, not built)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (executed the current-state ▶ Next-action candidate; the broader
  residence guard was *routed*, not built)
- **↪ Next:** an ungated lane — consistency-linter AI-nav PR 1 (needs runtime + hermes-review),
  the other small guards, or a fresh plan-first lane; the residence-guard ratchet awaits the
  owner decision above

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1163, pending auto-merge on green) |
| CI-red rounds | 0 (only the by-design born-red session gate) |
| Repo-rule trips | 1 (invalid doc badge token `partially-built`, caught by `check_docs --strict`, fixed) |
| New ideas contributed | 1 (cross-allowlist drift guard) |
| Ideas groomed | 1 (cogs-layer-view-residence-guard: direct-View half built, residence half routed) |
