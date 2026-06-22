# Idea — close the loop: instrument shipped features with the metric their design-sim assumed

> **Status:** `ideas` — capture only, **not a plan, not approval**. Source + binding contracts win.
> **Subsystem:** none (agent-workflow / meta).

## The idea

When we use a Monte-Carlo simulation to design a feature (e.g.
`tools/sim/fishing_minigame_sim.py`, whose *entire* recommendation rests on the assumed Discord
latency-chain constants `NET_DOWN/UP_*`, `RT_*`), the sim is only as trustworthy as those
assumed constants — and right now nothing ever checks them against reality. The idea: **whenever a
feature ships off a design sim, also ship a tiny bit of telemetry that logs the exact quantity the
sim assumed**, so a later session can replay live data through the sim and confirm (or correct) it.

Concretely for fishing: when the reel button is clicked, log the bot-measured `bite → click` round
trip (one structured log line / a cheap counter — no PII). After a week of real play, feed the
distribution back into the sim's `NET_*`/`RT_*` constants and re-run. If the real window-fairness
curve matches §2 of the design doc, the recommendation is *validated*; if not, we re-tune before
investing further. This makes a simulation **self-verifying** instead of a one-shot guess.

## Why it's worth having

- It directly operationalises the repo's own rule that **a tool's output must be verified against
  ground truth before it's trusted** (CLAUDE.md CI-parity §6; the Q-0105 "unverified — confirm a few
  times" header). A design sim is exactly such a tool, and today it has no ground-truth path.
- It's cheap (one log line at an existing seam) and turns every design sim from a disposable
  artifact into a durable, falsifiable model — the kind of self-improving-loop work the project
  treats as first-class.
- Generalises beyond fishing: any future "we simulated it to pick the numbers" feature (drop rates,
  cooldowns, matchmaking) gets the same one-line discipline → "log the assumed quantity."

## Lifecycle / next step

Small + decided-lane once any sim-designed feature ships. The minimal version is a convention
("design-sim PRs add a one-line telemetry counter for their load-bearing assumption") + a short note
in the sim's own header. Could later graduate into a checklist item in the relevant skill. Disposable
per Q-0105 if it proves to add noise rather than signal.
