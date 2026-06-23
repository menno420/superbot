# Session — 2026-06-23 · Close the new-subsystem checker's blind spots

> **Status:** `in-progress` — born-red HOLD card; flip to `complete` as the final step.

**Run type:** owner-directed. **Branch:** `claude/peaceful-franklin-klgw3f`.
**Trigger:** after the Karma build (PR #1332), the owner approved implementing the
"new-subsystem ripple" idea. On investigation, a scaffold + checker already exists
(`scripts/new_subsystem.py`, fronted by the `/new-subsystem` skill) — so the real value is
**auditing it against the Karma ground-truth and closing the gaps it misses**, not building a
parallel tool.

## What I'm about to do

Running `new_subsystem.py check` against the now-fully-wired `karma` surfaced **two** things:
1. A genuine drift in PR #1332 — karma is missing from `docs/repo-navigation-map.md` (the checker
   caught it). **Fix:** add the karma row.
2. The checker has **blind spots** — it does *not* verify three touch-points that actually broke
   Karma's CI (each cost a round of red): the **sector-folio map** (`docs/repo-sector-map.md`),
   the **extension-role overlay** (`architecture_rules/extension_roles.yaml`), and **config.py
   `INITIAL_EXTENSIONS` loading**. **Fix:** add those three checks to `build_checks`.

Deliverables: extend `scripts/new_subsystem.py` (+ its `tests/unit/scripts/test_new_subsystem.py`),
add the karma nav-map row, update the `/new-subsystem` skill's touch-point count, and re-badge the
`audited-score-subsystem-scaffold` idea (the generator half already existed).

## What changed

Tooling + docs only (no `disbot/` runtime change):
- **`scripts/new_subsystem.py`** — three new touch-point checks in `build_checks`:
  `extension-loaded` (cog is in `config.INITIAL_EXTENSIONS`), `extension-role` (key classified in
  `architecture_rules/extension_roles.yaml`), and `sector-folio` (conditional: if
  `docs/subsystems/<key>.md` exists it must be homed in `repo-sector-map.md`). Added the
  `_folio_homed_to_sector` helper (mirrors `check_sector_map.py`'s block parse), the two relevant
  enumeration tests to the printed verify set, and updated the header docstring.
- **`docs/repo-navigation-map.md`** — added the missing **karma** row (the real #1332 drift the
  checker itself caught).
- **`tests/unit/scripts/test_new_subsystem.py`** — 3 new tests (new checks pass for a fully-wired
  subsystem; loader/role attach for any cog while sector-folio is skipped when no folio; the
  `_folio_homed_to_sector` helper). 13 pass.
- **`.claude/skills/new-subsystem/SKILL.md`** — touch-point list updated to name the three additions.
- **`docs/ideas/audited-score-subsystem-scaffold-2026-06-22.md`** — re-badged *partially implemented*:
  the general scaffold already existed; this PR closed its blind spots; the score-specific
  `RankProvider` **parity guard** remains the open half.

**Why this shape (not the originally-flagged "new doc"):** investigation found a scaffold/checker
already exists (`scripts/new_subsystem.py`, `/new-subsystem` skill). Per do-not-duplicate (Q-0101) +
verify-against-source (Q-0120), the higher-value move was auditing it against the Karma ground-truth
and extending it — which immediately paid off by catching a genuine nav-map drift in #1332.

⚑ **Self-initiated:** none — owner approved implementing the idea ("you can implement it").

Verification: extended checker run against karma reports **all touch-points present ✓** (with
`--no-panel`); `check_quality.py --full` green.

## 💡 Session idea (Q-0089)

**Make `new_subsystem.py check` a CI guard, not just an on-demand tool.** The checker now encodes the
full touch-point list, but it only runs when an agent remembers to invoke it. A tiny test —
`for key in SUBSYSTEMS: assert build_checks(key, …) has no gaps` (deriving cog/panel from the registry
entry) — would turn the whole touch-point set into a standing invariant: any subsystem that drifts out
of `config.py` / `extension_roles.yaml` / the sector map / the nav map reddens CI automatically,
exactly like the existing per-touch-point enumeration tests do for their slice. The checker becoming a
test is the natural graduation of a now-proven guard (Q-0105 "verified" end-state). Deferred here only
to keep this PR's scope to *closing the gaps*; it's the obvious next slice.

## ⟲ Previous-session review (Q-0102)

The Karma build session (PR #1332) was thorough and shipped a fully-integrated subsystem, but it
**missed the `repo-navigation-map.md` row** — ironic, because the tool that would have caught it
(`new_subsystem.py check`) already existed and wasn't run during that build. The lesson isn't "try
harder"; it's that a guard nobody invokes is worth little. **System improvement (initiated):** this
session both fixed the drift *and* extended the guard, and the Q-0089 idea above proposes making it a
CI test so the next subsystem can't silently skip it — turning a discretionary checklist into an
enforced invariant.

## 📋 Doc audit (Q-0104)

- `check_docs --strict` + `check_quality --full` green.
- No merged-PR ledger impact (this PR not yet merged; next reconciliation records it).
- No new owner *decision* (a rule change) — the script docstring + skill are the durable home for the
  touch-point list; idea file re-badged.
- The nav-map drift is now fixed at its source (`repo-navigation-map.md`), not just noted.
