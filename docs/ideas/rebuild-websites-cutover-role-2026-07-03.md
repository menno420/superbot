# Idea — the off-Discord websites: rebuild disposition, cutover role, and staying current

> **Status:** `ideas` — capture (owner-originated). **Subsystem:** none (off-Discord surface /
> operations). **Provenance:** owner idea-drop, 2026-07-03, after the Fable-5 final judgment
> (PR #1701). Closes judgment gap §4 #4 (the off-Discord surface has no rebuild disposition and
> structurally dies at cutover) and serves gaps #16 (owner-consumable visual artifacts), #9/#11
> (cutover user-comms). Source wins over this doc (Q-0120).

## The gap the judgment found

The shipped **public bot site** (`botsite/` — marketing, `/changelog`, interactive command
reference) and the **developer dashboard** are fed by one producer,
`scripts/export_dashboard_data.py`, which **AST-parses the OLD repo** (`disbot/utils/
subsystem_registry.py`, `docs/bot-changelog.md`, `.sessions/*.md`). Nothing in the rebuild plan
dispositions them, so at cutover the new repo has no equivalent producer and **both sites go stale
or die** (judgment §4 #4). The owner's insight closes this and turns it into an asset.

## The owner's insight — the sites are useful *during* the switch, and must stay current

1. **A cutover-comms surface.** The public changelog site is the natural public face of the
   in-server release announcer (companion idea
   `rebuild-release-testing-loop-2026-07-03.md`) — the "what changed / what to test" story for
   users who aren't in a test channel, and the user-facing communication CUT-3 currently lacks
   (judgment §4 #9/#11).
2. **A progress + verification dashboard.** During the multi-month dual-repo build, the dashboard
   can track **rebuild progress** (Stage-2 rows walked, subsystems triaged, `verified_live`
   coverage, parity-golden pass rate, open owner-gated decisions) — which is also the
   **owner-consumable visual artifact** the judgment flagged as missing (§4 #16: every gate hands a
   non-coder, visually-oriented owner prose/JSON with nothing rendered).
3. **They must stay updated with progress** — so their producer has to become a first-class,
   maintained part of the rebuild, not an afterthought that rots.

## Disposition (the rebuild answer)

- **Repoint the producer at the new repo's manifest.** The new bot's **declared surface is a
  cleaner data source than AST-parsing** — the command reference, changelog, and coverage all fall
  out of the manifest + the release/coverage stores (idea A/B), so the sites are *generated from the
  same declarations as everything else*. This is the repo-as-artifact framing (Q-0234 part 3)
  applied to the sites.
- **Decide which site stays vs merges** (fork): the public marketing/changelog site and the
  internal dev/progress dashboard may want different hosting, update cadence, and audiences during
  the dual-repo interim.
- **Give it a cutover role in D-3/CUT-3:** the public changelog + a status page are part of the
  user-comms and progressive-exposure plan the judgment flagged as absent (§4 #11 / stress D-3).

## Open forks (resolve when promoted)

1. **Interim producer:** does the site keep reading the *old* repo until cutover, switch to the
   *new* repo's manifest as soon as it has a surface, or run both side-by-side (old = live bot, new
   = progress)? (Ties to the frozen-reference / old-bot-interim policy, judgment §4 #21.)
2. **Hosting + update cadence** during the dual-repo months — and who/what regenerates it (a
   routine? a CI step on merge?).
3. **Scope of the progress dashboard** — how much of the Stage-2/verified_live/owner-queue state it
   surfaces, and whether it's public or owner-only.

## Routing

- A rebuild-scoped disposition item: fold into the **Stage-3 consolidation** (the sites are part of
  the cutover + repo-as-artifact story) and give the producer a home in the new repo's manifest
  consumers.
- Pairs with `rebuild-release-testing-loop-2026-07-03.md` — the sites are the off-Discord surface
  for the same announce/coverage data.

## Pointers

- Judgment gaps this closes: `final-judgment-fable5-2026-07-03.md` §4 (#4, #16, #9/#11).
- Shipped producer to port: `scripts/export_dashboard_data.py`; sites under `botsite/`.
- Framing: Q-0234 part 3 (repo-as-artifact) · D-3/Q-0222 (cutover).
