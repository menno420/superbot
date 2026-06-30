# 2026-06-30 — BTD6 track lengths (Red Bloon Seconds) + estimator escape-margin

> **Status:** `in-progress`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**Branch:** `claude/ai-answer-storage-plan-3fvdit` (restarted from main; PR #1574 merged).
**Run type:** manual (owner-directed).

## What I'm about to do

The owner asked me to web-search the **track length for red bloons in seconds** — the one gap the
boss-fight estimator (#1574) was missing. Found it: the community-standard unit is **Red Bloon
Seconds (RBS)** — seconds for one Red Bloon (the speed-1.0 baseline) to cross a map's main track on
Medium. Pulled the **complete 61-map table** from the Bloons Wiki *Red Bloon Seconds* page via its
`api.php?action=parse` endpoint (the rendered page is Cloudflare-walled; the API isn't).

Building (verified-data, offline):
- **`disbot/data/btd6/map_track_lengths.json`** — 60 maps keyed to `maps.json` ids (Blons omitted —
  not in our maps dataset), with provenance (source URL, fetch date, the RBS definition).
- **Estimator integration** — a track-length lookup + an **escape-margin** in the estimate: a red
  bloon crosses in `rbs` s; a boss crosses in ~`rbs / boss_speed` s (labelled estimate, since boss
  speed is a multiple of the base bloon speed); compare against the tower's time-to-kill so the
  estimate says whether the tower kills it before one unobstructed pass.
- Tests (data integrity + the new estimate fields) + the corpus note that track length is no longer
  a gap.
