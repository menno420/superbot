# 2026-06-16 — dashboard `/status` page (live status & health surface)

> **Status:** `in-progress` — building the remaining Q-0156 read-only dashboard surface.

## Arc (what I'm about to do)

Scheduled DISPATCH run, empty work order → advance the next plan slice. The buildable `ready`
decade-queue is consumed and both open PRs (#929, #941) are `needs-hermes-review` carve-outs (not my
merge authority). The live active lane is the **developer dashboard** (owner explicitly wants to keep
building it). Per the dashboard plan's "⭐ Next session — start here", the remaining **read-only**
Q-0156 surfaces are *live status/health* + *games & economy*; `/games` shipped (#983), so the next
buildable slice is the **status/health** page.

Building `/status` — an operational at-a-glance surface, same low-risk shape as the other pages
(separate Railway service, never imports `disbot/`, reads committed `dashboard.json`, no migration,
no external egress):

- **Deployed build banner** — the git commit/subject/date the data was generated from (answers "is my
  latest merge live?", the owner's headline "live status" ask). New `meta.build` in the export
  (git-derived, guarded → empty on failure).
- **Health summary grid** — the 11 inventory counts as cards linking to their detail pages.
- **Bug health** — open vs fixed from `bugs[].status` (the "is something wrong?" signal).
- **Access tier distribution** — subsystems per visibility tier.

Touches: `scripts/export_dashboard_data.py` (+`meta.build`) · `dashboard/app.py` (`/status` route) ·
`dashboard/templates/status.html` (new) · `base.html` nav · regenerated `dashboard.json` · smoke +
export tests · dashboard plan de-stale.
