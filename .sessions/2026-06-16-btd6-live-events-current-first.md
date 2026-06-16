# Session — BTD6 Live Events: fix the dead drill-down + current-event-first redesign

> **Status:** `in-progress`

## What I'm about to do

Owner shared a Discord screen recording of the BTD6 **Live Events** browser. Two complaints:
1. "it does not look nice, it's not easy to understand … this should be properly divided into clear
   informational views that display **only the current event** and **all information available about
   it**."
2. "the race event button **still does nothing**."

Diagnosis from the video + source:

- **Root cause of "does nothing" (a real crash):** `services.btd6_view_model_service.
  build_event_detail_view_model` calls `btd6_db.search_facts(entity_kind=…, entity_key=…, limit=2)`,
  but `search_facts(*, fact_type=None, entity_kind=None, limit=50)` has **no `entity_key`
  parameter** → `TypeError` on **every** event drill-down (race/boss/ct/odyssey/event). The select
  callback already deferred the ephemeral, so the exception leaves it un-updated → "nothing happens."
  The path had **zero test coverage**, so it shipped broken.
- **UX problem:** the browser lists *all* stored facts (mostly `status: ended`) via
  `build_event_list_view_model`, capped at 25, ordered by fetch time — a wall of dead events with
  cryptic API ids, the same data duplicated in the embed *and* the dropdown, and no focus on what is
  actually live. `get_active_events()` already filters to live/future events but the browser ignores
  it.
- **Latent secondary bug:** `cogs.btd6._event_helpers.build_event_payload` looks up boss metadata
  with `{id}_normal`, but ingestion stores it as `{id}_standard` (`difficulty="standard"`), so boss
  event detail never finds its rules/restrictions.

Plan:
1. **Fix the crash + enrich detail** — rewrite `build_event_detail_view_model` to use
   `get_latest_fact` for the index fact and the correct per-kind metadata fact (race
   `btd6.race_metadata`; boss `btd6.boss_metadata`/`btd6_boss_difficulty`/`{id}_standard`; odyssey
   `btd6.odyssey_metadata`/`btd6_odyssey_difficulty`/`{id}_easy`), so detail renders full rules +
   tower/hero restrictions for all kinds.
2. **Current-event-first landing** — new `build_live_overview_view_model()` (live events only, strict
   future-end filter matching the hub panel) + a `LiveOverviewView`: an embed showing the live event
   per kind (or "nothing live"), a select containing **only** the currently-live events → rich
   detail, and a de-emphasized **📜 Past events** button that opens the existing kind-picker/list
   browser (history, also → the same rich detail). Nobody is stranded: history has a ↩ back to live.
3. **Fix** the `_normal`→`_standard` boss-metadata suffix in `_event_helpers`.
4. Tests for all three (the previously-uncovered detail path included).

## What was done

(to be filled in as the deliberate final step)

## 💡 Session idea

(pending)

## ⟲ Previous-session review

(pending)
