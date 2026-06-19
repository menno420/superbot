# /route-idea

Classify a raw idea and file it into the backlog the right way — the idea-intake step the maintainer
does constantly (Q-0089/Q-0172 capture-and-classify), turned into one command.

## What this does

Takes a raw idea (a sentence the maintainer or an agent dropped) and routes it into the
`docs/ideas/` conveyor per `docs/ideas/README.md`: dedup-check it, pick the right home (a line in an
existing capture vs. its own file), index it in the README, and — only when the owner has actually
decided something about it — leave a router stub. This is the intake half of the idea lifecycle; it
does **not** approve or build anything. Wrapper around the existing `docs/ideas/README.md`
procedure, not new policy.

> Capture-and-classify is mandatory even when an idea arrives mid-task: an idea raised mid-stream is
> *captured and classified first* (that discipline keeps the backlog reviewable) but does **not**
> derail the current task (Q-0172). Routing != implementing.

## Invocation

```
/route-idea "leaderboards should auto-post weekly to a configured channel"
```

Pass the idea as the argument.

## Instructions for Claude

### Step 1 — dedup first

`grep` `docs/ideas/` **and** `docs/roadmap.md` for the idea's keywords. If it already exists, add to /
sharpen the existing capture rather than creating a duplicate, and stop.

### Step 2 — classify + pick a home

- **Small note / one line** -> add a bullet to the most relevant existing capture file in
  `docs/ideas/` (e.g. a cog gap -> `cog-improvement-audit-*.md`; a workflow tweak -> the relevant
  workflow idea doc).
- **Substantial / its own thread** -> create `docs/ideas/<topic>-<date>.md` with the `ideas` badge
  header that states what it is **not** (not a plan, not approval), one line of *why it's worth
  having*, and `-> relates` pointers to the source files/subsystems it touches.

### Step 3 — index it

Add a one-line entry to the `docs/ideas/README.md` bullet list (provenance: who raised it + date + the
Q-number if owner-directed; the one-line why; the `-> relates` pointers). The README is the conveyor
index — an unindexed idea is an orphaned idea.

### Step 4 — router stub *only if the owner decided something*

If the idea carries an owner **decision** (a "do this" / "don't do this" / "the answer is X"), record
that decision in `docs/owner/maintainer-question-router.md` as the next free `Q-00NN` (append-only).
Do **not** open a router Q just to ask permission to build — promotion no longer needs approval
(Q-0172); only genuine owner-intent ambiguity goes to the router.

### Step 5 — report

Print: home (file path) · indexed (Y) · router stub (Q-number or "none") · dedup result. The idea is
now routed; *grooming* (`/groom-ideas`) is what later moves it down its lifecycle.

### Notes

- Routing is **capture without commitment** — nothing in `docs/ideas/` is approved by being filed
  there. Source code, the binding contracts, and `docs/current-state.md` always win.
- Forced filler is worse than none (the Q-0089 bar): if the "idea" is empty, say so rather than
  manufacturing a capture file.
