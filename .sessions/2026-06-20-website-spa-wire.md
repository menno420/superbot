# 2026-06-20 — Wire the Claude-designed SPA into the bot site (live data)

> **Status:** `in-progress`

## Arc

Owner uploaded `SuperBot_Design_System.zip` — a Claude-Design handoff containing a finished
vanilla-JS SPA (neon theme: Home / Features / Commands / Games / Changelog / Status) whose only
wire-up task per its README is to regenerate `prototype/data.js` from the real bot. Owner asked to
"make sure the current state of the website will be built and linked to the current botsite, follow
the Claude-design instructions to provide the proper data, eventually all data should dynamically
load," and invited a better/more-efficient approach (owner is still learning Claude Design).

**Decision (owner via AskUserQuestion):** SPA becomes the served bot-site front-end; data delivered
via a **dynamic FastAPI endpoint + a committed generated fallback**. The efficiency win: instead of
hand-writing `data.js` (instant drift), **generate it from the existing CI-guarded `site.json`
pipeline** so it stays truthful with zero manual upkeep.

## Plan (what this PR adds)

- `botsite/site/{index.html,app.js,app.css}` — the design SPA, copied **verbatim** (handoff rule:
  do not edit these; only the data layer).
- `botsite/site_data.py` — stdlib-only generator: `site.json` (public subset) → the SBDATA
  contract (ICONS/AREAS/COMMANDS/GAMES/CHANGELOG/STATUS + lookup helpers + `window.SBDATA`).
  Lives inside `botsite/` so the runtime endpoint can use it (Railway deploys only `botsite/`).
- `botsite/site/data.js` — generated committed fallback (so the SPA also opens as a static file).
- `botsite/app.py` — `/` serves the SPA shell; `/app.js`,`/app.css` static; **`/data.js` dynamic**
  (generated from live `site.json` per request); legacy page routes redirect into the SPA hash.
- `scripts/export_dashboard_data.py` — also regenerates the committed `data.js` (one pipeline).
- Tests: rewrite `test_app.py` for the new `/`; add `test_site_data.py` (contract invariants,
  CI-running, stdlib-only). Docs: `botsite/README.md`.

## Suggestions surfaced to owner

- The SPA's "Add to Discord" CTA is `href="#/"` (design placeholder). The handoff forbids editing
  `index.html`/`app.js`, so wiring the real install URL should originate from the next Claude-Design
  round (a 1-line change), or via a future `install_url` field the SPA reads. Flagged, not patched.

## ⚑ Self-initiated

None — owner-directed (wire the design into the site + dynamic data). Approach choices confirmed
via AskUserQuestion.

<!-- close-out (idea / previous-session review / run report / telemetry) appended as the final step -->
