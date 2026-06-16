# Idea: align our session success proxy with the research's "verified success"

> **Status:** `ideas`

**Captured:** 2026-06-16 · **Context:** readout of Anthropic's "Agentic coding and
persistent returns to expertise" research (~400K Claude Code sessions), owner asked
whether anything in it is usable here (Q-0089 session ender).

## Observation

The report's strongest outcome metric is **verified success** — sessions backed by
*hard signals*: tests passing, commits landing, explicit user confirmation — as
opposed to a model merely *judging* a session successful. It found verified success
is what separates expert from novice outcomes (≈28–33% vs ≈15%).

Our workflow already has an analogue: a session is "done" only when its PR reaches a
terminal state, and the terminal state is driven by **CI-green + auto-merge** (Q-0103
/ Q-0123) plus the born-red→flip-green session gate (Q-0133). That is the same
philosophy — *don't trust a self-judged "looks done," require a hard signal.* The
report is external validation that this is the right success definition to optimize.

## Proposal (small / low-stakes)

A one-line audit, not a new mechanism: confirm our hard signals actually cover the
report's three. We have tests-passing (CI) and commits-landing (auto-merge) well;
the third — **explicit owner confirmation** — is currently implicit (silence + green
CI merges the PR). Worth a deliberate check of whether any *class* of session should
require an explicit owner ack before auto-merge arms (e.g. anything touching binding
rules already routes through `needs-hermes-review` / `do-not-automerge` — so the seam
may already exist and just needs to be named as "this is our verified-success-with-
human-confirm lane").

## Value

Mostly confirmatory — the report says our success definition is the empirically
right one, which is reassuring rather than action-forcing. The contained value is
making the "which sessions need human confirmation vs. CI-only" boundary explicit
rather than emergent.
