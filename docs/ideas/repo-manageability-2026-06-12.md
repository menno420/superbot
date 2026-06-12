# Repo-manageability ideas — 2026-06-12

> **Status:** `ideas` — captured when the owner asked "what else would make the repo more
> easily manageable?" after the review-map + readiness-map work. These are about the
> *dev/review workflow* (the substrate), not the bot's features.
>
> **Update 2026-06-12 (owner-approved):** ideas **#1, #2, #3, #5 are EXECUTED** as
> `scripts/{review_scope,_review_units,readiness_scoreboard,check_doc_freshness}.py` +
> the `current-state.md` trim/archive + the `check_docs` Recently-shipped ratchet
> (see [`context-map-tooling.md`](../context-map-tooling.md)). **#4 (folio coverage)
> remains a discuss item.**

The review-map (#715) + the seven readiness maps (#717–#723) made the repo *navigable* and
*reviewable per slice*. These ideas target what's still friction. Each is dedup-checked
against existing docs/tooling.

## 1. Operationalize the review-map in tooling *(already captured — cross-ref)*
Make `context_map.py` print a file's review unit, add a PR-level `review_scope.py`. Fully
specified in [`review-unit-tagging-2026-06-12.md`](review-unit-tagging-2026-06-12.md).
**The single highest-leverage follow-up** — it turns the review partition from a doc you
must remember into a signal the toolchain emits. Quick-win lane.

## 2. Trim + auto-archive `docs/current-state.md`
**Problem:** `current-state.md` is the **2nd doc every session reads**, but its header is a
single enormous run-on "▶ Next action" paragraph (the repo already split some lanes after
they "collided on every parallel merge"), and "Recently shipped" grows unbounded (now back
to ~#660). Reading it is slow; editing it collides.
**Idea:** (a) cap "Recently shipped" to the last ~15 entries and auto-archive older ones to a
`docs/current-state-archive.md` (the journal already uses this archive pattern); (b) finish
breaking the mega-header into the per-lane bullets the file itself recommends. A tiny
`check_docs` soft-ratchet on the header/Recently-shipped length would keep it lean.
**Why:** faster orientation + fewer parallel-merge collisions on the hottest doc. Quick-win
lane; touches a high-traffic doc so confirm the cap number with the owner.

## 3. Freshness guard for dated snapshots (audits / readiness maps)
**Problem:** the seven readiness maps (and other `audit`/`plan` dated docs) are point-in-time
— they silently rot as source moves. Nothing flags a stale map.
**Idea:** a `check_docs`-adjacent check: for any doc whose name/header carries a date and an
`audit`/`plan` badge, warn (never fail) if the source paths it cites have git-changed since
that date — "this map may be stale; re-verify before trusting." Pairs with the gap-analysis
"toolchain rot watch" item.
**Why:** keeps the new review/readiness investment from decaying into misleading docs.
Quick-win lane (read-only, git-log based).

## 4. Folio / context-pack coverage for the smaller subsystems
**Problem:** there are **7 folios** (+7 generated context packs) but ~31 cog subsystems. An
agent on `economy`, `moderation`, `xp`, `role`, `inventory`, `counting`, etc. has the
navigation cheat-sheet + ownership, but **no single-page area entry** like the 7 big areas.
"Read only your subsystem" is uniform for 7, ad-hoc for the rest.
**Idea:** either (a) generate a lightweight stub folio/context-pack per remaining subsystem
from the cheat-sheet + registry + ownership rows, or (b) decide the cheat-sheet is
sufficient for small cogs and document that explicitly so the gap is intentional, not
accidental.
**Why:** completes the "every slice has one entry page" promise the review-map implies.
**Route: discuss** — could be over-engineering for tiny cogs; owner/lead call on a/b.

## 5. Readiness scoreboard (generated, one glance)
**Problem:** the readiness state now lives across seven maps; there's no single at-a-glance
"how production-ready is the bot?" view that updates as maps refresh.
**Idea:** a generated Done/Partial/Not-Done tally per subsystem (parsed from the maps' status
tables) rendered into the production-readiness README or `current-state.md`. Refreshes when a
track lands and a map's rows flip.
**Why:** turns the hardening roadmap's progress into a visible metric. Quick-win lane, but
depends on the maps keeping a parseable table shape (they do today).
