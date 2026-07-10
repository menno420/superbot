# Seat boot-verification harness — script the dispatch copilot's §5 row

> **Status:** `ideas` — session ender (2026-07-10, round-3 dispatch part 4).

## The observation

The dispatch copilot's per-seat verification ritual is now a **four-times-repeated
manual sequence** (fleet-manager, substrate-kit, idea-engine, product-forge — and
part 4 replayed it for the forge + sim-lab): check the trigger registry for the seat's
routine (name / cron / enabled / next fire), fetch the seat's `control/status.md`
heartbeat at HEAD via public raw, confirm expected inbox ORDERs / outbox entries, and
compose the runbook §5 row from the findings. Every step is mechanical; only the
verdict line needs judgment. With three games-Project seats incoming (Q-0259 r.5),
the ritual runs at least three more times.

## The idea

A small superbot script — `python3.10 scripts/check_seat.py <repo> [--routine <name>]
[--expect-order N] [--expect-outbox N]` — that:

1. pulls the account trigger registry (via the claude-code-remote MCP from a session,
   or takes a `list_triggers` JSON dump as input) and matches the seat's routine by
   name, reporting cron / enabled / next-fire / created;
2. raw-fetches `control/status.md` (+ `status-*.md`), parses the kit heartbeat grammar
   (`updated:` freshness, `kit:` line, `orders:` acked/done, `⚑ needs-owner` count);
3. raw-fetches `control/inbox.md` / `outbox.md` and checks expected entry numbers;
4. emits a ready-to-paste **runbook §5 row skeleton** with every verified fact filled
   and `[[fill: verdict]]` left for judgment.

Grounded in the Q-0120 doctrine: the script only reports transport-verifiable facts
(registry, git @ HEAD) and explicitly labels self-reported ones (status content) so
the copilot can't accidentally launder a self-report into a verification.

## Why it's worth having

The §5 rows are the fleet's boot audit trail; hand-composing them is where transcription
drift enters (part 2's six-vs-seven lesson was exactly a hand-composed state error).
One command per seat also makes the every-wake re-verification (brief §2.4 class) cheap
enough to actually happen. Natural home: superbot `scripts/` next to the other checkers;
consumers: every future dispatch/copilot session.
