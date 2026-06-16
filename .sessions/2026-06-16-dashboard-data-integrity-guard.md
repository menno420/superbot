# 2026-06-16 — dashboard.json integrity guard

> **Status:** `complete` — tooling + tests only (no `disbot/` runtime, no dashboard templates).
> One PR (#990).

## Arc

The owner is shipping the control-panel **write path** (mutation endpoints) and the **website OAuth
+ editors** in parallel sessions, and asked me to continue with **something non-conflicting**. I had
just started scoping the control-API *read* endpoints — but those live in `disbot/control_api.py`,
exactly where the mutation-endpoints session is working, so I **pivoted to avoid the collision**
(syncing `main` first also revealed #989 had already landed the control-API foundation — I'd nearly
duplicated it). Picked a slice touching neither `control_api.py` nor the website OAuth/editor pages.

## Shipped (PR #990)

- **`scripts/check_dashboard_data.py`** — a stdlib integrity guard for the exported `dashboard.json`
  (the bot's main website's data, now extended by many parallel sessions):
  - **cog→subsystem resolution** — every real (`is_cog`) cog's `subsystem` resolves to a registry
    subsystem key, minus a curated allow-list of legitimately-unregistered cogs (BTD6 sub-cogs ·
    Hermes · Paragon · Setup · RPS) and modules/mixins. A *new* unregistered cog / broken join errors.
  - **count integrity** — `meta.counts.*` match the actual array lengths (the #973 count-drift class).
  - **required fields** — every command has a name + valid `type`; every cog a `file`; every
    catalogue entry a `key`.
  - CLI: validates the committed JSON, or `--fresh` regenerates from live sources first (so a newly
    added unregistered cog is caught even if the JSON is stale). Q-0105 provenance header.
- **`tests/unit/scripts/test_check_dashboard_data.py`** — per-check synthetic drift cases + a live
  guard validating the **freshly-built** export has no error-severity issues (the in-CI value).

Directly motivated by #988: acronym cogs whose `subsystem` didn't resolve rendered with a generic
icon + no routing key, invisibly — this turns that class into a failed check.

## Status checklist

- [x] `scripts/check_dashboard_data.py` (validate + CLI, Q-0105 header)
- [x] `tests/unit/scripts/test_check_dashboard_data.py` (synthetic drift + live-export guard)
- [x] executed Q-0089 coverage-check idea → shipped; README updated
- [x] `check_quality --check-only` + the new tests green
- [x] session enders + flip card `complete`

## Verification

- `python3.10 -m pytest tests/unit/scripts/test_check_dashboard_data.py` → **7 passed**.
- `python3.10 scripts/check_dashboard_data.py` → OK (42 cogs, 0 errors); `--fresh` → OK.
- `python3.10 scripts/check_quality.py --check-only` → green (resolved one black↔ruff `COM812`
  trailing-comma tension by running `ruff --fix` after black); `check_docs --strict` → green.
- Sanity: the unit tests prove the guard *catches* a new unregistered cog / count mismatch / bad
  field (not just passes on clean data).

## 💡 Session idea (Q-0089)

**Map sub-cogs to their parent subsystem** —
`docs/ideas/dashboard-subcog-parent-subsystem-2026-06-16.md` (+ README). The guard *allow-lists* the
~7 real cogs that don't resolve to a registry key, but several genuinely *belong* to a parent
(`BTD6EventsCog`…→`btd6`; `RockPaperScissorsCog`→`rps_tournament`) — so on the dashboard they render
with a generic 🧩 + no routing key. A small explicit cog→parent-subsystem override map in
`scan_commands` would let them inherit the parent's identity and shrink the allow-list to the
truly-unregistered few. Genuine — I saw it directly while curating the allow-list.

## ♻️ Backlog grooming (Q-0015)

Moved the **dashboard-registry-coverage-check** idea (filed last session, #988) all the way to its
**terminal state — shipped** (this PR's main task literally executed it, broader than sketched: a
full export integrity guard, not just the cog-resolution check). Updated its file Disposition +
README entry to SHIPPED #990. Moving an idea `ideas → shipped` is the cleanest grooming move there is.

## ⟲ Previous-session review (Q-0102)

Reviewed **`2026-06-16-control-api-foundation.md`** (#989 — the bot-side control API that landed
between my #988 and this session, and the work I almost duplicated). **Did very well:** it nailed the
*safety shape* for adding a risky runtime surface to a production bot — **dormant by default**
(routes register only when `CONTROL_API_TOKEN` is set, so merge ≠ activation), **fail-safe wiring**
(a control-API error can never break health-server/bot startup), private-network + token auth, and a
crisp "how to activate" runbook. It also complied with repo invariants *properly* (used
`resolve_member`, registered in the atlas `TOP_LEVEL_MODULES`, regenerated `env-vars.md`) rather than
suppressing the checks. **Could've gone further / what it missed:** it didn't update
`docs/owner/active-work.md` with a claim — which is precisely why I started scoping the *same* control
API a session later before catching it via `git log`. The claim ledger is the *pre-PR* duplicate-work
signal (Q-0126); a runtime-foundation PR that other sessions will obviously build on most needs one.
**System improvement it surfaces:** the near-duplication wasn't caught by the claim ledger (no claim)
— it was caught by *me syncing main first*. The thinner, more reliable guard would be **"sync `main`
+ scan `git log` for the feature area before scoping any runtime work,"** because a merged PR is a
harder signal than a claim that may never be written. The orientation already says scan open PRs;
adding *recently-merged* `main` commits to that pre-flight scan would have caught #989 immediately.
(Captured as the workflow note; CLAUDE.md is propose-only.)

## Documentation audit (Q-0104)

- Two idea files filed/updated + README-indexed (coverage-check → shipped; sub-cog parent map → new);
  `check_docs --strict` green. The guard's provenance is in its own header (Q-0105) + this card.
- No owner decision this session (a non-conflicting tooling pivot, owner-directed "continue with
  something non conflicting"), so no router Q-block needed.
- **Ledger untouched (Q-0124):** the merged-PR backlog is the automated reconciliation routine's job;
  my own PR (#990) isn't merged yet. Nothing from this session lacks a durable home.

## Context delta

- **Sync `main` + scan `git log` before scoping runtime work** — #989 (control-API foundation) had
  merged with no active-work claim; I nearly rebuilt it. A merged-commit scan of the feature area is
  the reliable duplicate-work guard when a claim is missing.
- The dashboard's cog→subsystem join has ~7 real cogs that don't resolve to a registry key (BTD6
  sub-cogs · Paragon · RPS · Setup · Hermes) — now allow-listed by the guard and captured as the
  parent-subsystem follow-up idea. New unregistered cogs beyond these will fail the guard's live test.
- The control API is **dormant until `CONTROL_API_TOKEN` is set on both Railway services** (#989) —
  the read/write endpoints + OAuth the owner is building in parallel are what switch the panel on.
