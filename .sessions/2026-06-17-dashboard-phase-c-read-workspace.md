# Session — dashboard Phase C: the read workspace (personal overview + server health + authority preview)

> **Status:** `complete`

## What I'm about to do (born-red declaration, Q-0133)

Scheduled dispatch, empty work order → advance the active thread. The night/BTD6 queues are consumed;
the **dashboard lane is the live thread** (Phase E read endpoints shipped #1013; R3 hardening is in
flight on #1014, another session — *not* mine to touch). The remaining buildable dashboard slice the
Phase E log + the finalized-vision plan both name is **Phase C's read workspace** — skipped when the
build jumped C-auth → F-writes:

- `/me` — a logged-in **personal overview** (the hinge between the public site and per-server
  management): who you are + the servers you administer, each linking to its overview.
- `/admin/{guild}/overview` — a **read-only per-server health summary** (invalid settings,
  customisations, help overrides, disabled cogs) — the non-editing companion to the editor.
- an honest **authority preview** ("what you may read / change here") from the authority bridge.

All **read-only**, over the already-shipped Phase E read endpoints (`/control/settings/current`,
`/control/help/overlay`, `/control/routing`) + the authority bridge — **no new bot-side endpoints**,
no runtime hot-path, no editor-form changes (so no overlap with #1014's CSRF work). New routes +
templates + a pure `_setup_health` / `_authority_preview` projection, dashboard-only.

## What shipped (PR #1015 — Phase C read workspace)

All in `dashboard/` — **read-only, no new bot endpoints, no `disbot/` code** (so no overlap with
#1014's editor-form CSRF work):

- **`/me` — personal overview** (`me.html`): greets the logged-in user, lists the servers they
  administer as cards (each → Overview + Manage), and an honest "what you can do here" note. Pure
  session data — no per-guild bot calls, so it stays fast for a user with many servers. Redirects to
  `/admin` when logged out.
- **`/admin/{guild}/overview` — read-only per-server health** (`admin_overview.html`): an authority
  preview ("what you may read / change here", from the authority bridge) + a setup-health summary
  (settings tracked · customised-from-default · invalid→using-default with names · help overrides +
  Home customised · disabled cogs with names) computed from the Phase E reads (`_fetch_current_state`).
  Honest per-widget states: dormant (not connected), `unavailable` (bot unreachable — the freshness
  contract's state + the previous session's control-link self-check idea, for free off the `authority is
  None` signal), not-a-member, and the live summary.
- **Pure projections** in `app.py`: `_setup_health(current)` + `_authority_preview(authority)` (no I/O,
  unit-tested) + a `_blank_current()` helper (de-duped the editor route's inline blank shape).
- **Navigation**: a "My overview" nav link (logged-in), Overview/Manage buttons on the `/admin` picker
  cards, and an Overview breadcrumb on the editor.

**Verification:** `check_quality --full` green (10408 passed) · `--check-only` green · arch 0 errors ·
+13 dashboard tests (routes, redirects, the live-reads render, the unreachable banner, and the two pure
projections), run for real under `python3.10` with fastapi installed (CI `importorskip`-skips them).

## Handoff — dashboard ▶ next

Phase C is done; the dashboard lane is at a natural boundary — every remaining slice is in-flight or
needs its own focused session:
- **R3 live-surface hardening** (rate-limiting + CSRF) — **in flight on #1014** (another session). Do
  not duplicate.
- **Phase D — manifest spine** (Q-0162): typed command/panel/settings manifest + panel registry +
  reconciliation tests; gates command/panel *management* (the AST `button_backed` weakness), not the
  shipped settings/help/routing editors. A real runtime investment — its own session.
- **Global-settings runtime tier** (Q-0157): touches the hot `resolve_setting` path → a focused runtime
  PR, deliberately not batched.
- Then **H** (panel-layout engine + editor), scheduled last (needs D + a panel registry).

## 💡 Session idea (Q-0089)

**A per-server "config drift" badge sourced from the manifest spine (Phase D).** Once the manifest
exists, the server overview's setup-health card could add a *binding-completeness* row: "N capabilities
have no role/channel binding here" (the authority preview already hints "the bot is missing this
binding" per the vision doc). Today's health card covers settings/help/routing; the missing dimension is
*unbound capabilities* — the #1 silent-misconfiguration class (BUG-0012 was exactly a missing-binding
fallback). It's a natural Phase-D consumer: the manifest knows each command's capability requirements,
so the overview can show which are unsatisfied for the guild. Small, read-only, high signal — worth a
`docs/ideas/` entry when D lands. (Dedup-checked: not in the vision doc's roadmap, which lists the
authority preview but not a binding-completeness health metric.)

## ⟲ Previous-session review (Q-0102) — #1013 (dashboard Phase E read endpoints)

**Did well:** scoped tightly and honestly — it explicitly de-scoped R3 + Phase C to follow-up PRs in
its own born-red card rather than cramming an overnight batch, which is exactly why *this* session had a
clean, well-documented seam to pick up (the read endpoints + `_fetch_current_state` were ready to
consume). The "see-then-change" framing was the right abstraction. **Missed / could-improve:** it built
the read endpoints and wired them into the *editor* (`/admin/{guild}`) but didn't surface them on a
read-only landing — so until this PR there was no place to *see* a server's state without entering edit
mode, and no honest "bot unreachable" state anywhere (a silent failure the freshness contract names).
**System improvement:** the dashboard lane now has three parallel-ish slices (E #1013, R3 #1014, C
#1015) from overnight dispatches — the claim ledger (`docs/owner/active-work.md`) would have made the
R3-vs-C split visible *before* I had to discover #1014 via `list_pull_requests`. Worth reinforcing in
the dispatch routine: when a lane is being worked by multiple overnight fires, append the claim *first*,
so the next fire reads intent without an open-PR scan.

## 📋 Doc audit (Q-0104)

- De-staled `dashboard-vision-finalized-state.md` — Phase C row + reviewer note now read **shipped**
  (#1015), not "partly shipped / still open".
- Added the #1015 Recently-shipped entry to `current-state.md` with the dashboard ▶ next handoff.
- **Ledger note (not mine to fix):** SessionStart flags 6 merged PRs not yet in `current-state` — the
  band-#990 reconciliation pass is next due at #1020 and is the **docs-reconciliation routine's** job
  (Q-0124: a dispatch session does not run the recon pass). Left for that routine.

