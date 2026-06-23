# 2026-06-23 — Settings centralization: a static settings-reachability guard

> **Status:** `complete` — owner-directed (the last unstarted item in the five-part consolidation
> goal). Builds the **static settings-reachability guard** — the settings analog of the #1370 command
> guard — so "every cog's settings reachable from the `!settings` hub" (brief §3.4) becomes
> un-regressable. PR this session; auto-merge armed on green (Q-0127); owner-directed → merge immediately
> (Q-0191).

> **Run type:** `manual · owner-directed`

## Finding (code-verified, no live bot)

The settings surface is already **structurally centralized**, but it was only *checkable* via a live-bot
catalogue build (`customization_catalogue.build_catalogue(bot)` needs loaded cogs — static `bot=None`
over-reports 41/41). The AST-verifiable facts:

- **19 subsystems declare a `SubsystemSchema`** (`cogs/*/schemas.py`) → auto-dispatched into `!settings`
  via `actionable_settings_groups()`. **All 19 are reachable** (non-internal + homed) — 0 gaps.
- **3 subsystems have a `.configure`/`.settings.*` capability but no schema:** `counting` + `chain`
  (per-**channel** game enablement, configured in their own `!countingmenu`/`!chainmenu` panels — a
  bespoke per-channel data model, *not* a guild-scalar setting) and `channel` (`channel.visibility.configure`
  is an admin **action**, not stored config). These are **intentionally domain-panel-configured**, not a
  centralization gap → explicit allowlist with reasons (mirrors how #1370 allowlists reachable-via-panel
  commands).

So there is no schema to *add* (inventing one for per-channel game setup would be wrong); the work is the
**guard + documented allowlist** that pins the boundary and fails CI if a *new* subsystem adds a schema
but isn't homed, or grows a `.configure` capability without either a schema or an allowlist entry.

## Deliverable (mirrors #1370)

- `scripts/check_settings_reachability.py` — static guard (registry + AST scan of `cogs/*/schemas.py`).
- `architecture_rules/settings_reachability_exceptions.yml` — allowlist (counting/chain/channel + reasons).
- `tests/unit/invariants/test_settings_reachability.py` — the CI invariant (warn-first ratchet baseline).
- `docs/audits/settings-reachability-2026-06-23.md` — the finding + exemption ledger.

## Close-out

**Verification:** `check_quality --full` green — **12164 passed**; `check_settings_reachability` →
19 reachable · 3 exempt · 0 GAP; new invariant (5 cases) green; ledger + `check_docs --strict` pass
(Q-0104 — the new audit doc is linked from the brief §3.4, no orphan). No `disbot/` runtime change, so
mypy/architecture unaffected. Merged the GitHub branch-auto-update (#1384 btd6, disjoint) before close.

**💡 Session idea (Q-0089):** *Graduate the settings-reachability guard to `--mode strict` in CI once it's
run clean across a couple of sessions* — same lifecycle the `edit_in_place` rule followed (warn→error).
The guard is already strict-clean (0 gaps, baseline empty); the only reason it isn't wired into
`check_quality`/CI as a hard gate yet is the Q-0105 "prove it quiet first" discipline. A future session
should add it to the quality run's strict set so a new decentralized-config subsystem *fails the build*,
not just a test — closing the loop on "settings stay centralized." (Captured; small follow-on.)

**⟲ Previous-session review (Q-0102):** the previous session (this same chat, PRs #1382/#1383 — the
never-stranded nav + game-result continuations) did well to *fix the checker in the same PR as the
mechanism* (#1383 taught the `back_button` rule about auto-nav), which is exactly the "checker and
mechanism must not drift" lesson it recorded. What it could have surfaced earlier: the broader
consolidation plan had a *measurable remaining list* (`current-state/S1-bot.md` line 65) that I only
re-grounded in when the owner asked for status — a session ending should always re-read its sector's
`▶ Remaining` line and name the next item, not wait to be asked. **System improvement (applied):** this
session opened by re-deriving the plan state from the authoritative ledger before acting, and picked the
last unstarted item deliberately. Worth making routine: end-of-session, restate the sector's remaining
queue so the chain is self-navigating.

**Claim** `docs/owner/claims/claude__settings-centralization.md` deleted at close (Q-0126).

