# Idea — band-archetype classifier in the reconciliation pass record

> **Status:** `ideas` — raised by the band-#1440 Q-0107 reconciliation pass (2026-06-24).
> Lane: S4 (docs system) / S3 (the engine's tooling). Size: small, `ready`-adjacent (extends the
> planned-slice hit-rate tracker idea).

## The problem

Three of the last four Q-0107 passes scored some variant of *"~0–1/N of the forward queue executed;
the band was owner-directed off-queue work"*:

- **band-#1440** (this pass) — the 13-PR **Essential Setup wizard restructure**, owner's live focus all day.
- **band-#1410** — a 4-merge micro-band, the new ticket subsystem (owner-directed).
- **band-#1380** — fishing + card-engine, mostly owner-steered.

This is **not a failure** — the §4 queue is a *menu*, not a *schedule*, and owner-directed work is the
highest-priority lane by design (Q-0191). But every pass re-derives the same observation by hand
("buffer became the band again"), and the owner never gets a *trend*: across the last 5–10 bands, how
much of the roadmap did the autonomous fleet actually drive on its own vs. how much did the maintainer
steer live? That ratio is exactly the **"is the workflow self-improving / self-driving?"** signal the
whole loop exists to surface — and right now it lives only as a repeated prose impression.

## The idea

Have each pass record open with a one-line **band archetype** tag, computed from two numbers the pass
already establishes in its scorecard:

- `slices_shipped` — how many named §4 slices from the *previous* pass's queue shipped this band
  (the planned-slice hit-rate tracker already computes this).
- `owner_directed_merges` — how many of the band's merges were owner-directed / off-queue.

From those, a cheap classifier:

| Archetype | Condition |
|---|---|
| `queue-executing` | most merges trace to named §4 slices |
| `owner-directed` | most merges are off-queue owner-steered work |
| `mixed` | a real split |
| `micro` | a small band (< ~6 merges, regardless of source) |

Emit it as the first line of the pass record's §1 (and optionally append it to the run-report footer),
so over time a trivial grep across `reconciliation-pass-*.md` yields the trend the owner actually wants:
*"7 of the last 10 bands were owner-directed"* → the fleet still needs steering; *"queue-executing is
rising"* → the autonomous loop is starting to drive the roadmap itself.

## Why it's worth having

It turns a per-pass prose impression into a **trend-able, owner-facing metric of autonomy** — the
single most important thing this self-improvement loop is supposed to be measuring about itself. It's
nearly free: it reuses the planned-slice hit-rate tracker's parse (one feeds the other) and adds one
derived line. Pairs with `planned-slice-hit-rate-tracker` (the per-slice detail) and the
`new-subsystem-followup-tracker` (which feeds the queue from shipped depth so `queue-executing` bands
become reachable). Subsystem: S4/S3 tooling.
