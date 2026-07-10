# Project capability self-awareness — ask a seat what it can do, get an honest answer

> **Status:** `ideas` — owner-raised (2026-07-10, round-3 dispatch part-4c), routed two
> ways: platform ask → EAP wrap-up email §(d) item 2 + §(g) evidence bullet
> (`../eap/gen1-wrapup-email-final-candidate.md`); fleet-internal mitigation → this file.

## The owner's words (verbatim, 2026-07-10)

*"the projects are not fully aware of how they work themselves yet, which would be a
good improvement, if you could just ask a project what it's abilities are, and it could
answer honestly, that would be really nice"*

## The incident that prompted it

sim-lab's freshly-booted coordinator found neither `create_trigger` nor `send_later` in
its toolset (verbatim wall recorded in its status OA-003), filed an owner-manual ask —
then a worker it spawned minutes later had both tools and armed the seat's failsafe
first-try (registry-verified). Same Project, same minute, different capability worlds,
no way for either party to know in advance. Fourth+ occurrence of the class
(idea-engine, Builder, forge each hit seat-dependent variants).

## Two halves

1. **Platform ask (routed to the EAP email):** a first-party, queryable, honest
   capability manifest per session — which tools exist, which permission tier applies,
   what the classifier will actually allow — or minimally, the model told its own
   toolset truthfully at session start.
2. **Fleet-internal mitigation (buildable now):** a kit `bootstrap.py capabilities
   --probe` command that runs the known probe battery (scheduler tools present? worker
   seat differs? merge path shape? raw-read reachability?) and REGENERATES the repo's
   `docs/CAPABILITIES.md` from live results with dates + verbatim errors — turning the
   hand-maintained ledger into a re-runnable self-test. A seat's calibration could then
   open with "my probed abilities are: …" — the honest self-answer the owner asked for,
   built from the outside until the platform provides it from the inside.

## Why it's worth having

The trial-and-refusal discovery tax recurs at every seat boot (four founding packages
now carry a worker-seat-retry recipe purely as a workaround); a probe battery makes the
cost one command, and its output doubles as EAP evidence.
