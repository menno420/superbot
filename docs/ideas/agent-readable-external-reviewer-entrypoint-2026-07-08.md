# Idea — a first-class "external agent reviewer" entry point into the repo

> **Status:** `ideas` · raised 2026-07-08 (EAP email two-reviewer session) · workflow/docs

## The trigger

The EAP email now invites Anthropic to point **a Claude session** at our public repo to review and
extend our findings (the "two reviewers" idea — a human + an agent). That surfaced a gap: our repo is
organized for *our* agents (who get `CLAUDE.md` + orientation auto-injected), not for an **external**
agent arriving cold with no context and no injected instructions.

## The idea

Add a single, stable, top-level entry point designed for an **external agent reviewer** —
e.g. `EXTERNAL-REVIEWER-START-HERE.md` (or `docs/eap/README.md` for the EAP specifically) — that:
- states what the repo is and what's worth verifying, in a few lines;
- links the load-bearing evidence (probe report, evaluation log, session cards, the self-audit report);
- lists concrete, checkable tasks ("confirm finding X reproduces from report Y", "does the record in
  `.sessions/` support claim Z");
- is written assuming **zero injected context** — the reader is an agent that has never seen our
  `CLAUDE.md`.

## Why it's worth having

- Makes the email's "put an agent on it" ask *actually easy to act on* — the reviewer has a front door.
- Generalizes past the EAP: any time we ask an outside party (human or agent) to audit our work, a
  cold-start entry point is the difference between "they find what we meant" and "they bounce."
- It's the external mirror of our own `AGENT_ORIENTATION.md` — same principle (make the repo
  self-orienting), aimed at a reader who doesn't get our injected rules.

## Dedup

Distinct from `docs/AGENT_ORIENTATION.md` (internal, assumes injected `CLAUDE.md`) and the session
self-audit idea (which produces *data*; this produces the *front door* to it).
