# Extend the auto-merge enabler to dependabot PRs

> **Status:** `ideas` — captured 2026-07-04 (open-PR review sweep session, PR #1719).
> **Subsystem:** none

## The problem this session hit

Six dependabot PRs (#1555–#1560) sat open for **five days** — all but one had green CI the whole
time. The `auto-merge-enabler` workflow only arms native auto-merge on `claude/*` PRs (Q-0123),
so dependency bumps pile up until a human or a sweep session dispositions them. Stale dependency
PRs also rot: while they sat, adjacent-line edits to `requirements.txt` created merge conflicts
(#1560 needed a manual resolve), and dependabot itself closed-and-recreated the group PR (#1556 →
#1720), doubling the review surface.

## The idea

Extend `auto-merge-enabler.yml` to also arm auto-merge on `dependabot/**` PRs. The existing
safety net already does the right thing:

- **CI is the gate:** auto-merge only fires when the required `code-quality` check is green —
  and CI installs the bumped deps and runs the full 14k-test suite, so a green dependabot PR is
  a *verified* dependabot PR (that is exactly the evidence this sweep merged them on).
- **The tool-pins guard holds the dangerous class:** a group bump that touches
  `requirements-dev.txt` tool pins alone (the #1074/#1315/#1556 drift class) fails
  `tool-pins` + `code-quality`, so auto-merge simply never fires — it waits for a session to do
  the three-place alignment. No new risk.
- Optional conservatism: arm only for patch/minor update types (dependabot exposes
  `update-type` metadata via `dependabot/fetch-metadata`), leaving majors (like Pillow 11→12)
  for a session to verify — though CI green covered that case fine this time.

## Why it's worth having

Removes a whole standing chore class (dependency-PR babysitting), shrinks the open-PR set that
every session must scan for overlap, and prevents the conflict/recreation rot that stale
dependency PRs accumulate. One small workflow edit; reversible; the kill-switch is deleting the
branch filter again (Q-0105 posture).

## Owner gate

Workflow edits are owner-gated (Q-0194 ownership split) — route via a router DISCUSS Q or ship
in an owner-directed session.
