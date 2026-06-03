# BTD6 game-file extraction — plan & handoff

> **Status:** PLAN ONLY — no extraction code written yet. Parked at the
> **recon** step (the user runs it on their tablet; see § "Step 1").
> This is a *roadmap* doc (read for context); when it disagrees with the
> source, the source wins.
>
> **Last updated:** 2026-06-03 (session that shipped the Steam patch-notes
> feed + the patch-notes diff tool — see § "What already shipped").

---

## ⚡ UPDATE 2026-06-03 — the decryption path is SUPERSEDED (verified)

A public repo, **`Btd6ModHelper/btd6-game-data`**, is the committed output of
BTD Mod Helper's built-in **"Export Game Data"** dumper — i.e. the game's
internal model JSON, **already decrypted** and published. This collapses the
entire risky middle of the plan below (locate assets → UnityPy → AES key →
IL2CPP) to **`git clone`**.

**Independently verified in-sandbox (commit `a3348a89`, dumped 2026-06-02,
message "55.0"):**

- **Anchors pass exactly** (the Phase-2 gate): Dart Monkey base `cost=200.0`,
  Super Monkey base `cost=2500.0`.
- **Coverage is complete** — every one of the 11 wiki-missing heroes is
  present with full per-level data (e.g. `Towers/Benjamin/Benjamin 2.json`,
  `cost=1200.0`, full `TowerModel`, 40-48 files each), and **both** prose
  paragons are real files: `Towers/Druid/Druid-Paragon.json` and
  `Towers/IceMonkey/IceMonkey-Paragon.json` (cost 400).
- **It's current** — the dump is at **v55.0**, dumped the day before this
  note; *more current than bloonswiki*, which had 0 towers at 55.0.
- **Layout**: `Towers/<Name>/` holds the base `<Name>.json` (tiers `[0,0,0]`),
  one file per crosspath state `<Name>-PPP.json`, and `<Name>-Paragon.json`;
  heroes use per-level `<Name> N.json`. Top level also has `Upgrades/`,
  `Bloons/`, `Rounds/`, `Bosses/`, `paragonDegreeData.json`, `textTable.json`
  (display names), etc. ~9,900 files, ~320 MB.
- **Schema** = the raw IL2CPP `TowerModel`: top-level `cost`, `range`, `tier`,
  `tiers`, and a `behaviors[]` list whose `$type`s include `AttackModel`
  (combat data nested under weapon → projectile → damage/pierce).

**What's resolved vs. the original open questions:** decryption (no key
needed), scoped storage / Termux / UnityPy / rooting (no device extraction
needed), and "untestable in sandbox" (the data is reachable here, so the
mapper can be built and tested end-to-end in-repo).

**What genuinely remains — the mapper (unchanged effort).** The hard part was
never decryption; it's projecting the verbose, deeply-nested `TowerModel`
onto our `stats/<id>.json` schema. Upgrade costs derive cleanly from the
crosspath files (cost(tier) − cost(prev tier) along a path); names from
`textTable.json`; the per-tier combat stats live in the nested `AttackModel`
tree and are the bulk of the work.

**Freshness fallback (Phase 5).** The dump refreshes only when a maintainer
re-runs the export, not automatically on patch day. It's still strictly
better than bloonswiki (whole-model at once, complete). For true day-one
self-sufficiency, run the same "Export Game Data" button yourself on the PC
build via **BTD Mod Helper + MelonLoader** — far easier than the original
Android/UnityPy path. Use the patch-notes feed (PR #459) to know when a fresh
pull is due, and `btd6_patch_diff.py` (PR #460) to verify the dump's currency.

**Legal note (even lower risk now):** you're consuming a public dump of
factual stat numbers, not extracting/decrypting anything yourself — same
category as how bloonswiki sources its data. Still commit only derived stat
values with provenance; do not vendor the 320 MB raw dump into the repo.

**Revised next step:** clone `Btd6ModHelper/btd6-game-data`, build
`scripts/parse_gamedata.py` mapping one tower (`dart_monkey`, anchor-proven)
then one gap hero (`benjamin`) onto our schema, validate against anchors,
wire in as a source above bloonswiki with provenance. The original
Android-extraction sections below are kept for context but are **no longer
the primary path**.

---

## Why this exists (the problem)

The BTD6 cog's structured stats (`disbot/data/btd6/stats/*.json`) come from
**bloonswiki.com** via `scripts/fetch_bloonswiki.py`. That source has two
real weaknesses we hit head-on:

1. **Timing lag.** After a game patch, bloonswiki updates *per-tower, over
   hours-to-days*. Verified live on 2026-06-03: with BTD6 v55 released that
   day, **zero** towers on the wiki were stamped `55.0` (newest was `54.0`;
   many towers still at `53.0`/`52.2`).
2. **Coverage gaps — the wiki simply doesn't have the data.**
   - **Only 6 of 17 heroes** have per-level stat modules: `adora`,
     `geraldo`, `gwendolin`, `quincy`, `sauda`, `striker_jones`. The other
     **11 have no module**: `admiral_brickell`, `benjamin`,
     `captain_churchill`, `corvus`, `etienne`, `ezili`, `obyn_greenfoot`,
     `pat_fusty`, `psi`, `rosalia`, `silas`.
   - **2 of 13 paragons** are hand-transcribed from prose (flagged
     `is_prose_sourced`): **Root of all Nature** (Druid) and **Herald of
     Everfrost** (Ice Monkey) — the wiki 404s their stats modules.

## Why patch notes can't fix this (settled)

Patch notes (Steam / r/btd6) are **deltas, not full state** — a changelog,
not a snapshot. You cannot reconstruct a tower's complete stat block from
them (no anchor for the unchanged ~95% of values; many lines are
non-numeric "reworked"/"increased"). Worse for the gaps: a hero that isn't
rebalanced appears in **zero** notes, so notes can never fill a hole the
wiki has. Patch notes are good for *maintenance/verification*, not baseline
construction.

**Source accuracy ranking: game files > bloonswiki > patch notes.**
Game-file extraction is the only source that is both **complete** (covers
the 11 heroes + 2 paragons) and **day-one accurate** (no wiki lag).

## What already shipped (the interim / maintenance layer)

These handle "stay current between patches" while the wiki catches up; they
do **not** replace the need for a complete source:

- **PR #459 (merged):** Steam `ISteamNews/GetNewsForApp` ingestion (appid
  `960090`, no API key) → `btd6_patch_notes` + a `btd6.version_detected`
  event → `services/btd6_version_announce` posts to a configured channel
  (`!btd6ops announcechannel`). Gives the *prose notes* + a "new version
  dropped" signal immediately.
- **PR #460 (open, CI green):** `scripts/btd6_patch_diff.py` — parses notes
  text, verifies each `old > new` against the on-disk stat files, and
  buckets changes (CLEAN/LIKELY/STALE/REVIEW/NO_FILE/SCOPE). Turns each
  patch into a reviewable worklist; never auto-applies.

---

## The extraction approach

BTD6 is **Unity / IL2CPP**. Gameplay data (towers, upgrades, bloons,
rounds, **all heroes, all paragons**) ships as **AES-encrypted JSON
`TextAsset`s** inside the Unity assets. The decryption key is a game
constant (lives in the native binary — `libil2cpp.so` on Android,
`GameAssembly.dll` on PC), so an **Android extraction yields identical data
to PC**.

Pipeline:

1. **Locate** BTD6's asset files on the device.
2. **Extract** the `TextAsset`s — Python **UnityPy**.
3. **Decrypt** — AES with the community-known key. *This is the crux / the
   one genuinely uncertain step.*
4. **Validate** against known anchors before trusting anything (e.g. Dart
   Monkey base cost = `200`, Super Monkey = `2500` — cross-check a handful
   against the current committed files).
5. **Map** the game-model JSON → our `stats/<id>.json` schema (a
   `parse_gamedata`-style module, analogous to `parse_bloonswiki.py`).
6. **Commit** with clear provenance; re-run each patch.

**Payoff:** complete coverage (17/17 heroes, 13/13 paragons), exact, day-one.
**Cost:** re-run per patch (assets change; occasionally the key/format
shifts), and step 3 may need iteration.

## Environment & device facts

- **Claude runs in an ephemeral cloud sandbox** with *no game files and no
  way to fetch them*. Claude **cannot run the extraction** — it builds the
  tooling/mapper/tests and integrates; the **user runs extraction on their
  device** and feeds back decrypted-JSON samples to iterate on.
- **Device:** Samsung Galaxy Tab S11 Ultra (Android), keyboard + mouse.
  **BTD6 is installed** (Play Store build). **NOT rooted.**
- **On-device toolchain:** **Termux** (install from **F-Droid**, not Play
  Store) → `pkg install python` → `pip install UnityPy` (may need native
  deps: lz4 / brotli / Pillow build tools first).

## Division of labor

| Claude (in repo) | User (on tablet) |
|---|---|
| Extractor + decrypt + mapper scripts (`scripts/`) | Set up Termux + Python + UnityPy |
| Schema mapping + validation harness + tests | Get at BTD6 asset files; run scripts |
| Pipeline integration + provenance flags | Paste decrypted-JSON samples; iterate on decryption |

---

## Step 1 — RECON (do first, on the tablet, in Termux)

Cheap, safe, no decryption. Tells us whether the gameplay data is **inside
the APK** (easy, no scoped-storage problem) or in **external downloaded
bundles** under `/sdcard/Android/data/...` (harder on Android 11+ without
root). Paste the output back.

```bash
# 1. Confirm it's installed + the package name
pm list packages | grep -iE "ninjakiwi|bloons"

# 2. Where are the APK(s)?  (use the package id from step 1)
pm path com.ninjakiwi.bloonstd6

# 3. Pull the base APK and look for Unity data assets inside
cp "$(pm path com.ninjakiwi.bloonstd6 | head -1 | cut -d: -f2)" ~/btd6.apk
unzip -l ~/btd6.apk | grep -iE "bin/Data|\.unity3d|resources|\.assets|globalgamemanagers" | head -30

# 4. Sizes — APK vs external data dir (external may be blocked; that's fine)
du -h ~/btd6.apk
ls -laR /sdcard/Android/data/com.ninjakiwi.bloonstd6/ 2>/dev/null | head -40
```

## Phased plan (after recon)

- **Phase 0 — recon** (above): confirm format/location on the actual device.
- **Phase 1 — extract**: UnityPy script to pull `TextAsset`s from the
  confirmed location.
- **Phase 2 — decrypt + validate**: apply the community AES key; confirm
  against anchors. *Gate: do not proceed until anchors match.*
- **Phase 3 — map**: game-model JSON → `stats/<id>.json` schema; start with
  one tower end-to-end (e.g. dart_monkey) to prove the mapping, then a hero
  the wiki lacks (e.g. `benjamin`) to prove the gap is closed.
- **Phase 4 — integrate**: add as a data source (alongside/over bloonswiki),
  stamp provenance, wire into the existing CSV→JSON / data-service flow.
- **Phase 5 — maintain**: documented re-run procedure per patch.

## Open questions / risks

- **Scoped storage** (Android 11+): only an issue if data is *external* to
  the APK. No root, so we'd need a SAF-capable file manager to copy the
  app's `Android/data` to shared storage. Recon step 3/4 decides if this
  even matters.
- **Decryption key currency**: the community key may be stale if NK rotated
  it recently — validated against anchors in Phase 2.
- **Termux native deps**: UnityPy's lz4/brotli/Pillow may need manual
  `pkg install` of build tooling on ARM64.
- **Untestable in the sandbox**: Claude debugs partly blind; the user is the
  eyes on real files.

## Legal / licensing stance

- The bot is **free, non-commercial, mostly private servers**; future
  monetization is unrelated commissioned work (e.g. custom in-chat games),
  **not** this BTD6 data. This is the lowest-risk category for personal
  data-mining (same as how the wiki community sources its data).
- Raw stat **numbers are facts** (not copyrightable). BTD6's EULA prohibits
  reverse-engineering; extracting/decrypting assets is a gray area accepted
  for personal/informational use.
- **Do NOT commit** the AES key, the decryption routine sourced from the
  binary, or wholesale decrypted asset dumps to the repo. Commit only the
  **derived stat values** in our schema, with a `source` provenance note.
- This *replaces* bloonswiki's CC-BY-NC-SA "NC matters if monetized" concern
  with the EULA/RE one — acceptable given the non-commercial use above.

## Pick-up checklist for next session

1. Has the user run **Step 1 recon**? If yes, read their output → decide
   APK-vs-external path.
2. Confirm Termux + UnityPy install status on the tablet.
3. Proceed to Phase 1 (extract) → Phase 2 (decrypt + **validate against
   anchors**) before any mapping.
4. Companion docs: `docs/btd6-data-pipeline.md` (the bloonswiki pipeline this
   would augment/replace), `docs/btd6-data-backends.md`.
