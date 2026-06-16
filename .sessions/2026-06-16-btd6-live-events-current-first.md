# Session — BTD6 Live Events: fix the dead drill-down + current-event-first redesign

> **Status:** `complete`

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

PR **#953** (born-red → flipped complete). Diagnosed from the recording by extracting frames with
`imageio[ffmpeg]` (no ffmpeg in the env; installed for `python3.10`), then root-caused in source.

- **Fixed the crash (the "does nothing").** `build_event_detail_view_model` called
  `btd6_db.search_facts(entity_kind=…, entity_key=…, limit=2)` — but `search_facts` takes no
  `entity_key` kwarg → `TypeError` on **every** drill-down (proved via `inspect.signature`). The
  select had already deferred the ephemeral, so `HubView.on_error` swallowed it → silent no-op.
  Rewrote the builder to use `get_latest_fact` for the index fact + the correct per-kind metadata
  fact. The path had **zero coverage**; the one existing test mocked `search_facts` with a bare
  `AsyncMock` (accepts any kwarg) which masked the bug.
- **Current-event-first redesign.** New `build_live_overview_view_model()` (live events only, strict
  future-end filter matching the hub panel) + `LiveOverviewView`: a landing that shows what's live
  per kind with countdowns (or "_nothing live_"), a select of **only** live events → rich detail,
  and history moved behind a de-emphasized **📜 Past events** button with **↩ Live now** back-nav.
  Detail is colour-coded (green=live / grey=ended) and now renders full rules + banned/limited
  towers + disabled flags + scores + coverage.
- **Fixed a latent bug:** `_event_helpers.build_event_payload` looked up boss metadata as
  `{id}_normal`; ingestion stores `{id}_standard`, so `!btd6events event boss <id>` never found
  restrictions. Now `_standard`.
- **Tests:** crash regression (detail must not call `search_facts` with `entity_key`, must not
  raise), boss-metadata-suffix assertion, live-overview VM (live-only / strict filter), and the
  overview view/select/embed + history back-nav. `check_quality --full` green (**9990 passed, 37
  skipped**); mypy clean; arch 0 new violations.

Grooming (Q-0015): sharpened `docs/ideas/button-command-surface-parity-2026-06-16.md` — added the
**sibling failure mode** (a button whose callback silently crashes vs. a button with no command
front door) and scoped that idea away from it, routing the crash class to the new mock-fidelity idea.

## 💡 Session idea

`docs/ideas/autospec-mock-fidelity-guard-2026-06-16.md` — make project mocks signature-faithful
(`create_autospec` / `AsyncMock(spec=real_fn)`) via a lint/AST guard or a tiny `autospec_setattr`
helper, so a call-site kwarg typo the real function would reject also fails the test. Born directly
from this session: the drill-down crash shipped green **because** a bare `AsyncMock` was more
permissive than the real `search_facts`. Dedup-checked against `docs/ideas/` (no existing mock/spec
idea); README-indexed.

## ⟲ Previous-session review

The previous session (#952, `railway_logs.py` retry/backoff) was a clean, well-tested transport
hardening — injectable `sleep`/`max_retries`, fail-against-old tests, and it correctly *didn't* mask
real 4xx/GraphQL errors. Good restraint. What the chain could do better, and this session is the
proof: **a unit test that passes is not evidence the call works** — #952's tests were faithful
because they drove the real `post()`, but the BTD6 bug here shows the opposite pattern (a mock more
permissive than reality) shipping a 100%-broken user-facing feature green. **Concrete system
improvement:** adopt signature-faithful mocks for the service/DB facades (the new
`autospec-mock-fidelity-guard` idea) — the smallest durable change that would have turned this
production crash into a red test. (No filler: this is a genuine, specific gap the session surfaced.)
