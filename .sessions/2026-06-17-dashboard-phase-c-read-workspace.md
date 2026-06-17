# Session — dashboard Phase C: the read workspace (personal overview + server health + authority preview)

> **Status:** `in-progress`

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

## What shipped

_(to be filled at close)_
