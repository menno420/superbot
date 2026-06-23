# Hub child-rendering consistency + placement coherence (+ a panel-link guard)

> **Status:** `plan` — research + execution record for a **future, dedicated session**.
> Owner-directed (2026-06-23): after the treasury panel-link bug (#1344), the maintainer asked
> for "a plan … so I can do some research on it with a fresh session," and separately noted that
> "multiple subsystems/buttons [are] registered in multiple panels … some really only belong in
> one place … this should be a separate generalization session." Source code wins over this doc.
>
> **Subsystem:** none (this is platform/help-surface architecture, not a single bot subsystem).

## The ask (verbatim intent)

Two related problems the maintainer surfaced:

1. **Rendering inconsistency.** Treasury (#1334) was registered as an Economy `primary_child` with a
   `build_help_menu_view` hook and passed CI, yet had **no clickable button on any panel** — reachable
   only by typing. Root cause: some hub panels render their registered children automatically and some
   hardcode their buttons. "I thought anything that wasn't linked to a panel wouldn't go through" —
   the guard doesn't actually enforce that.
2. **Placement coherence.** Several subsystems/buttons appear in **multiple** panels. Not wrong by
   definition, but "some really only belong in one place." Wants a deliberate audit of where each
   thing lives.

This plan covers both, plus a **guard** so problem 1 can't recur. It is intentionally a *separate*
generalization effort — do **not** fold it into an unrelated feature session.

## Current state (mapped 2026-06-23 — verify against source before acting)

### A. Which hub panels render their children — the inconsistency

`utils/hub_registry.py` defines 7 hubs (`games`, `btd6`, `economy`, `moderation`, `community`,
`utility`, `admin`). Each declares `primary_children` (its own subsystems) and optional
`cross_link_children` (subsystems homed elsewhere, surfaced here too). Two rendering styles exist:

| Hub | View | Renders children dynamically? | Evidence |
|---|---|---|---|
| **games** | `views/games/hub.py` | ✅ **dynamic** | `discover_game_children()` + `_GameHubButton` + `_GROUP_ROW_STYLE`; reads `SUBSYSTEMS`. Farm got a button for free. |
| **community** | `views/community/hub.py` | ✅ **dynamic** | "discovers both groups from registry"; ~18 registry refs. |
| **economy** | `views/economy/main_panel.py` | ❌ **hardcoded** | Buttons (Daily/Work/Shop/Balance/Inventory/Jobs) are individual `@ui.button` methods; 0 registry refs. **inventory** + **treasury** (since #1344) are hand-coded; **leaderboard** has NO button. |
| **moderation** | `views/moderation/main_panel.py` | ❌ **hardcoded** | 0 registry refs — its 6 `primary_children` (automod, image_moderation, cleanup, logging, proof_channel, security) are not registry-rendered; audit which have buttons. |
| **admin → server_management** | `views/server_management/hub.py` | ❌ **hardcoded** | 0 registry refs. |
| **admin → diagnostic** | `views/diagnostic/hub_panel.py` | ❌ **hardcoded** | 0 registry refs. |

So **2 of 6 hubs auto-render children; 4 hardcode.** The hardcoded ones are where a registered child
can silently lack a button. `btd6` has no children; `utility` (general, four_twenty) — verify.

**Why CI didn't catch treasury:** `tests/unit/invariants/test_discoverability.py` only asserts each
subsystem has a `build_help_menu_view` hook **OR** a panel command **OR** `visibility_mode=internal`
— i.e. *openable by typing*. It does **not** assert a parent hub panel renders a clickable entry.
That is the precise gap.

### B. Multi-placement — the "registered in multiple panels" observation

`cross_link_children` is the intended mechanism for a subsystem to have ONE primary home + extra
surfaces. Current double-placements:

| Subsystem | Primary home (`parent_hub`) | Also cross-linked in | Earns the cross-link? (owner decides) |
|---|---|---|---|
| `mining` | games | economy | Plausible — mining is an economy activity. |
| `leaderboard` | economy | community | Question — is it wanted in both, or economy-only? |
| `counting` | games | community | Question — Games-only might be cleaner. |
| `chain` | games | community | Question — Games-only might be cleaner. |

These four are the "some really only belong in one place" cases to review. The decision is **product
taste**, not mechanics — which is exactly why it wants a research session with the owner in the loop.

## Proposed approach — 3 PRs (plan span ≤ 3)

### PR 1 — Generalize hub child-rendering (the foundation)

Extract the Games/Community dynamic-child-button mechanism into ONE shared helper so every hub
renders its registered children identically.

- **New** `views/hub_children.py` (name TBD): given a hub key, build one button per
  `primary_child` (and, per a flag, per `cross_link_child`) that routes to the child cog's
  `build_help_menu_view`. Generalize `views/games/hub.py`'s `_GameHubButton` + `discover_*` +
  `_GROUP_ROW_STYLE` + the back-attach closure (currently Games-specific:
  `attach_back_to_games_button`).
- **Retrofit the 4 hardcoded hubs** to call it. The hard part: Economy/Moderation panels mix *action*
  buttons (Daily/Work/Shop — these stay hand-coded) with *child-nav* buttons. The helper should append
  child-nav buttons on a **dedicated row**, leaving action buttons alone. Respect Discord limits
  (≤5/row, ≤25 components/view) and the existing `attach_back_to_<hub>_button` back-nav chaining.
- Then **delete** the now-redundant hand-coded child buttons (inventory/treasury on Economy) so there
  is ONE source of truth per child. Keep action buttons.
- **Risk:** these are core, heavily-used panels. Mitigation: retrofit **one hub per commit**, keep
  each diff small (CLAUDE.md: small PRs for risky runtime), add a view-level test per hub asserting
  every `primary_child` now yields a button. Games/Community already work — use them as the reference
  and ideally migrate them onto the shared helper too (so the helper has ≥2 proven consumers).

### PR 2 — The panel-link discoverability guard

Extend the discoverability invariant (or a sibling test) so the #1344 class is impossible to
reintroduce:

- For every hub, every `primary_child` must be **panel-linked**: either rendered by the shared helper
  (detect the helper call in the hub's view module) **or** a hand-coded `custom_id="<hub>:<child>"`
  button exists in the view module, **or** it is explicitly listed in a
  `architecture_rules/*.yml` exemption with a reason (mirrors the back-button allowlist pattern).
- Failing message names the offender + the three fixes (render via helper / add button / exempt).
- This guard would currently flag **leaderboard** (Economy primary_child, no button) — fix it in this
  PR (it's the live instance of the bug) by letting PR 1's helper render it.
- Carries the Q-0105 "unverified, delete if unreliable" provenance header until proven across sessions.

### PR 3 — Placement-coherence audit (decision doc + agreed cleanup)

The **owner-in-the-loop** part. Produce a decision matrix (one row per `cross_link_children` entry)
with a recommendation: *keep cross-link* / *demote to primary-home-only* / *move primary home*. Then
apply the agreed changes to `hub_registry.py` + `subsystem_registry.py` (keeping the bidirectional
roster rule intact — see `services/help_catalogue.py` `roster_drift`). Open as a router DISCUSS block
if intent is unclear rather than guessing taste.

Research questions to settle with the owner first:
- Should `cross_link_children` render as **buttons** at all, or be a lighter "see also" mention?
  (Today Community renders both groups as buttons — that's part of the perceived duplication.)
- Per double-placed subsystem (mining / leaderboard / counting / chain): keep both surfaces, or one?
- Should each hub visually separate **action** vs **navigate-to-subsystem** controls (rows/labels)?

## Out of scope / non-goals

- No new subsystems or game features.
- No change to the typed-command surface (`!treasury` etc. keep working regardless).
- The `btd6` and `utility` hubs unless the audit finds a real gap.
- Slash-command front door (a later S11 concern).

## Verification (every PR)

- `python3.10 scripts/check_quality.py --full` (true CI mirror) · `check_architecture --mode strict`.
- Per-hub view test: instantiate the hub view, assert one button per `primary_child`.
- The new guard (PR 2) green; `test_discoverability.py`, `test_help_surface_map_doc.py`,
  `test_hub_registry.py`, and the `help_catalogue` roster tests stay green.
- `check_current_state_ledger --strict` + `check_docs --strict` on close.

## Key files (turn-key pointers)

- `disbot/utils/hub_registry.py` — the 7 `HubEntry`s, `primary_children` / `cross_link_children`.
- `disbot/utils/subsystem_registry.py` — `SUBSYSTEMS`, each child's `parent_hub`.
- `disbot/views/games/hub.py` — the **reference** dynamic renderer to generalize
  (`discover_game_children`, `_GameHubButton`, `_GROUP_ROW_STYLE`, `attach_back_to_games_button`).
- `disbot/views/community/hub.py` — second dynamic renderer.
- `disbot/views/economy/main_panel.py` — hardcoded; `attach_back_to_economy_button` is the back-nav
  pattern to preserve. (The treasury button added in #1344 is the example to fold into the helper.)
- `disbot/views/moderation/main_panel.py`, `disbot/views/server_management/hub.py`,
  `disbot/views/diagnostic/hub_panel.py` — the other hardcoded hubs.
- `tests/unit/invariants/test_discoverability.py` — the existing (weaker) guard to strengthen.
- `disbot/services/help_catalogue.py` — `roster_drift` / `unknown_parent_hub` validation to keep green.

## Provenance

Captured by the economy-treasury panel-link session (2026-06-23, PR #1344). The single-button fix
shipped there is the *symptom* fix; this plan is the *root-cause* generalization the owner asked to
research separately.
