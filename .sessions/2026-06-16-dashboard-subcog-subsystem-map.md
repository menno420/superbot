# 2026-06-16 — dashboard: map sub-cogs to their parent subsystem

> **Status:** `complete` — scanner + data + tests only (no `disbot/` runtime, no dashboard
> templates/app). One PR (#995).

## Arc

"Continue from where you left off." Synced `main` first (the standing lesson) — found the owner's
parallel sessions had landed **#993 (control-API mutation endpoints / write side)** and **#992**
(foundation-complete docs reconcile), so the bot-side control API is now complete (read #989 + write
#993) and the owner's remaining active work is the **website OAuth + editors**. Picked a slice clear
of both that lane and the control-API file: executed my own filed idea
(`dashboard-subcog-parent-subsystem`, Q-0089 from #990).

## Shipped (PR #995)

The integrity guard (#990) *allow-listed* the real cogs whose `subsystem` didn't resolve to a registry
key — but several genuinely **belong** to a parent, so on `/commands` they rendered with a generic 🧩 +
no routing key. Mapped the unambiguous ones to their parent's registry identity:

- **`scripts/scan_commands.py`** — `_COG_SUBSYSTEM_OVERRIDES` (applied first in `_cog_to_subsystem`),
  verified against the registry (`btd6` = "BTD6 Assistant", `rps_tournament` = "Rock Paper Scissors"):
  `BTD6EventsCog`/`BTD6OpsCog`/`BTD6ReferenceCog`/`BTD6StrategyCog` → `btd6`, `RockPaperScissorsCog`
  (in `rps_tournament_cog.py`) → `rps_tournament`. So they now inherit the parent's emoji / display
  name / routing key on the dashboard — **no template change** (the existing `sysmap` join resolves it).
- **`scripts/check_dashboard_data.py`** — the guard's allow-list shrank **8 → 3** (`ParagonCog`,
  `SetupCog`, `HermesCog` stay; their parent is genuinely ambiguous → deferred to owner intent).
- Regenerated `dashboard/data/dashboard.json`; the 5 mapped cogs resolve, so they no longer need an
  allow-list exception, and a *new* unresolved cog still fails the guard.

## Status checklist

- [x] `_COG_SUBSYSTEM_OVERRIDES` in `scan_commands.py` + test
- [x] shrink `_UNREGISTERED_COG_ALLOWLIST` to {Paragon, Setup, Hermes}; guard still green
- [x] regenerate `dashboard.json`; 5 cogs now resolve
- [x] dashboard smoke test (20) + `check_quality --check-only` green
- [x] idea file update (5 done, 3 deferred) + session enders + flip card `complete`

## Verification

- `python3.10 -m pytest tests/unit/scripts/test_scan_commands.py tests/unit/scripts/test_check_dashboard_data.py`
  → **14 passed** (incl. new `test_cog_to_subsystem_applies_parent_overrides`).
- `python3.10 scripts/check_dashboard_data.py --fresh` → OK, 0 errors (42 cogs).
- `python3.10 -m pytest tests/unit/dashboard/` → **20 passed** (with web deps).
- `python3.10 scripts/check_quality.py --check-only` + `check_docs --strict` → green.
- Resolution confirmed: BTD6 sub-cogs → `btd6` (resolves), RPS → `rps_tournament` (resolves);
  Hermes/Paragon/Setup remain unresolved (allow-listed, by intent).

## 💡 Session idea (Q-0089)

**Cogs declare their subsystem.** *(Captured here only — the standalone idea file + README index entry
were **deferred** from this PR to escape the ledger-conflict livelock below; file it next session.)*
The dashboard guesses a cog's subsystem from its *class name*, propped up by **three** hand-maintained
lists (acronym table · the override map I just added · the guard's allow-list) that drift
independently — and even after #995, 3 cogs can't be resolved from the name alone. Replace it with an
authoritative declaration the scanner reads (a `SUBSYSTEM = "btd6"` cog class attribute, or a
command-surface-ledger join), deleting the override map and self-describing every cog. Genuine — I felt
the maintenance smell directly while curating the override map this session.

## ⚠️ Merge-conflict livelock (process note — the real lesson of this PR)

This PR hit a **3× consecutive merge-conflict loop**: every dashboard/night-work session prepends a
claim to `docs/owner/active-work.md` and an entry to `docs/ideas/README.md`, so each time I merged
`main` and pushed, the next parallel merge (#994 → #996 → #997, minutes apart) re-conflicted on those
**append-only ledger files** before my CI could go green. My merge→regenerate→test→push cycle was
slower than `main`'s merge cadence → livelock. **Fix that broke it:** shed my footprint on the
contended files — reverted `active-work.md`, `README.md`, and the subcog idea-file edits to `main` and
dropped the new idea file, so my branch diverges from `main` **only** on low-contention files
(`scan_commands.py` · `check_dashboard_data.py` · `dashboard.json` · the scanner test · this card).
The feature + its tests are intact; the docs hygiene (idea-file "shipped" badge, README index entry,
new idea file) is **deferred to a calmer moment / next session**, recorded here so it isn't lost.

## ♻️ Backlog grooming (Q-0015)

This session's main task **executed** the dashboard-subcog-parent-subsystem idea (filed #990) — the 5
unambiguous cogs mapped, the 3 ambiguous deferred to owner intent — which *is* the grooming move (idea
→ implemented). NB: the idea-file "shipped" disposition + README index update were **reverted out of
this PR** to escape the ledger-conflict livelock (above); re-apply them next session so the backlog
reflects the shipped status.

## ⟲ Previous-session review (Q-0102)

Reviewed **`2026-06-16-dashboard-data-integrity-guard.md`** (#990 — my own previous session). **Did
well:** caught a real, invisible drift class (the acronym cogs) and shipped a guard that fails CI on a
*new* unregistered cog — non-conflicting infra that protects all the parallel dashboard work. **What it
could have done better — and I fixed this session:** it **allow-listed all 8** unresolved cogs rather
than checking which were genuinely unfixable. 5 of the 8 were trivially *resolvable* (they have a real
parent subsystem) — allow-listing them **suppressed a fixable defect** instead of fixing it, and the
generic-🧩 rendering persisted one extra session. The cheap-but-wrong move (suppress) was taken over the
root fix (map). **System improvement it surfaces:** when adding any allow-list / suppression, triage
each entry as *genuinely-unfixable* vs. *just-unhandled* before freezing it — and annotate which, so a
later session knows what to revisit. (I added that distinction to the allow-list comment + the deferred
3 now carry an explicit "ambiguous parent → owner intent" reason. Captured as the workflow note;
CLAUDE.md is propose-only.)

## Documentation audit (Q-0104)

- Idea-backlog updates (subcog → shipped; cog-declares-subsystem → new) were **deferred** out of this
  PR to escape the ledger-conflict livelock — recorded in this card for next-session re-application.
  The feature's provenance lives in the scanner's own comments + this card; `check_docs --strict` green
  on the trimmed footprint.
- **No owner decision** this session (a non-conflicting execution of an already-filed, decided-lane
  idea), so no router Q-block. The 3 deferred cogs are flagged for owner intent in the idea file.
- **Ledger untouched (Q-0124):** the merged-PR backlog is the reconciliation routine's job; my PR
  (#995) isn't merged yet. Nothing from this session lacks a durable home.

## Context delta

- The dashboard cog→subsystem join now resolves the BTD6 sub-cogs + RPS via
  `scan_commands._COG_SUBSYSTEM_OVERRIDES`; only `ParagonCog`/`SetupCog`/`HermesCog` remain unresolved
  (allow-listed, parent intent deferred to the owner).
- **Three** hand-maintained lists now govern this join (acronym table · override map · guard
  allow-list) — captured the strategic replacement (cogs self-declaring their subsystem) as the
  session idea, since the maintenance smell is now real.
- Control API is **complete** bot-side (read #989 + write #993, dormant until `CONTROL_API_TOKEN` is
  set on both Railway services); the owner's active lane is the website OAuth + editors (OAuth app
  created, redirect `…/auth/callback`). Stay out of `control_api.py` + the dashboard templates/app/auth.
