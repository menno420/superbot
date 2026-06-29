# 2026-06-29 — Session-slug-uniqueness guard (close BUG-0027's residual clobber risk) + Mining how-to button

> **Status:** `in-progress`
<!-- born-red flow (Q-0133): in-progress while open; flip to complete as the final close step. -->

**Run type:** routine · dispatch

## What I'm about to do (born-red intent)
Empty-fire dispatch. Two contained, offline, self-mergeable slices:
1. **`check_session_slug_unique.py`** — the previous run's own Q-0089 idea (#1524). A
   `[session-close-gate]` checker that FAILS when a PR's session card path *already exists
   in `origin/main`* and the card is an active (non-re-badge) session card — catching the
   slug collision at author time so it never reaches the clobber+merge stage BUG-0027 hit.
   The gate fix (#1524) neutralized the *premature-merge* harm; this closes the residual
   *silent-clobber* harm at the root. Wire into `/session-close` Step 4 (the meta-check
   `check_session_close_gate.py` enforces the wiring stays).
2. **Mining how-to button** — the Mining completion cert's last build gap (✔-ready candidate);
   mirrors the Creatures how-to that closed #1546's cert.

Also: deleted the stale claim `funny-franklin-ca1e1q.md` (the already-merged #1524
RPS/Deathmatch/Chicken-farm session left it behind — docs drift, fix-on-sight Q-0166).
