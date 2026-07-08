# Rebuild Project — audit checklist (apply to every status report / PR batch)

> **Status:** `reference` · created 2026-07-08 by the directing session
> ([`rebuild-direction-handoff-2026-07-08.md`](rebuild-direction-handoff-2026-07-08.md))
> to make "did the Project do correct work?" a repeatable, falsifiable check instead
> of a vibe read of commit messages. Grew out of two things this directing session
> caught by actually reading source instead of trusting prose: (1) `superbot-next`'s
> `docs/current-state.md` is still the unfilled kit template — nobody is keeping the
> "what's done / what's tested" ledger the coordinator's own kit ships for that
> purpose; (2) the `question-router.md` V-5 block re-asked something `superbot`'s own
> router (Q-0244) had already ruled — a duplicate-work tell.

Run this against **every status report** (the cheap pass, ~5 min) and do the **deep
spot-check** (bottom section) roughly every 10 merged PRs, mirroring superbot's own
"every 30th PR" reconciliation cadence but tighter, because this run is moving faster.

## A. Directing quality (axis 1 — is it steering you correctly?)

- [ ] Owner-only items are **batched** into the question-router, not dripped one at a
      time or attempted-then-blocked. (Confirmed working as of #1–29: all six blocks
      landed in one file, each with options + a built safe-default.)
- [ ] Each router block cites **why the agent can't decide it alone** (genuine
      product/policy call, not something `docs/decisions.md` already settles).
- [ ] **No re-asked questions.** Before trusting a "pending" router block, grep
      `superbot`'s own `docs/owner/maintainer-question-router.md` and the target
      repo's own `decisions.md` for the same question already ruled elsewhere. (Caught
      once already — V-5(a) re-asked a Q-0244-ruled question.)
- [ ] `docs/current-state.md` in the target repo is an **actual living ledger** (In
      flight / Recently shipped / Stability baseline filled in), not the unfilled kit
      template. If it's still template text after several PRs, that's a process gap —
      flag it back, don't just read around it.
- [ ] Status reports arrive at real band boundaries with a clear "what shipped / what's
      next / what's waiting on you" shape — not a wall of commit-message prose.
- [ ] No destructive/production/owner-only action was *attempted* (force-push, secrets,
      Railway, CUT-2+) — only *flagged*. Check `list_commits` / `actions_list` for
      anything that looks like it tried and hit a wall, vs. cleanly deferred.

## B. Spec-correctness / build quality (axis 2 — is the work actually right?)

- [ ] **CI is green on the real gates** (`ci` / `test` workflows — the ones that
      actually run tests/checkers), not just "a workflow ran."
- [ ] A workflow that's *designed* to stay red (e.g. `golden-parity`'s `report` leg,
      red-until-parity by construction) is **not** mistaken for a build break. Check
      the workflow file's own comments before flagging red as a problem.
- [ ] **Spot-read at least one file per audit pass**, not just the commit message. Pick
      the PR with the boldest claim and open the actual diff. (This directing session
      read `tools/manifest_compile.py` against its D-0005 commit-message claims and it
      held up — but that's one file out of dozens; don't let one clean spot-check stand
      in for the next ten PRs.)
- [ ] Commit-message spec citations (`frozen L0 spec NN §X.Y`) actually say what the
      message claims, checked against the real spec doc at least occasionally — a
      confident, precisely-worded citation is not itself evidence (Q-0120: a green
      check — or a convincing citation — that contradicts what you can verify is a bug
      in the *claim*, not clearance).
- [ ] Test counts move in the direction claimed (commit says "172 unit tests green" —
      does the suite actually have that many, growing PR over PR, not static or
      shrinking while claims keep growing?).
- [ ] No file that a commit message describes at length turns out to be a stub,
      placeholder, or near-empty file. (Direct lesson from this session: I nearly
      pushed a docs file containing only the placeholder text `*** see file content
      above ***` instead of real content, and the API accepted it silently — file
      *size* after a push is a real, cheap corroborating signal, not busywork.)
- [ ] Each repo's own architecture/namespace/manifest checkers (`check_architecture`,
      `check_namespace`, `check_symbol_shadowing`, `manifest_compile.py --write`, …)
      are represented in CI and passing — don't just trust the commit message's "all
      N checkers green" line without seeing which checkers exist in `tools/` and
      confirming CI actually invokes them.

## C. What's-been-tested tracking (the thing that's currently missing)

- [ ] `docs/current-state.md` "Recently shipped" section names each landed band with a
      one-line verification note (tests green / manual smoke / not yet verified).
- [ ] `tools/check_verified_live.py --debt-list` (or equivalent) output is checked
      periodically — are any surfaces actually signed `VERIFIED` yet, or is the
      registry still 100% `unverified`? Track the trend, don't just confirm the
      registry *exists*.
- [ ] The `golden-parity` `report` job's ratio (ported/replayable subsystems out of the
      full corpus) is logged at each audit pass — 0/465 today; a healthy build should
      show this climbing once port bands start flipping subsystems to `ported`. A
      **stalled or shrinking ratio over several audits** is the single strongest
      leading indicator of drift outrunning verification.
- [ ] Manifest snapshot (`manifest.snapshot.json`) hash actually changes with each
      manifest-touching PR (P9 recompile-parity) — a stale hash next to new manifest
      claims is a compile-parity red flag.

## D. Process/repo hygiene

- [ ] No orphaned open PRs at audit time (everything merges same-session, per the
      coordinator's own forward-only-git instructions).
- [ ] No stale claim files if the coordinator is running multiple parallel workers.
- [ ] Decision ledger (`docs/decisions.md`) entries carry a `verdict` + `why`, not just
      a restated commit message.
- [ ] Repo settings (once configured by owner) — confirm required checks actually
      match what CI produces (job renames drift silently; re-check names each audit).

## How to use this

- **Cheap pass** (every status report): sections A + D, ~5 minutes, no code reading.
- **Deep pass** (~every 10 merged PRs): add B + C, including at least one real file
  read and one spec-citation cross-check.
- Log findings back into the directing session's own notes (not into the target
  repo's docs — this checklist audits *from the outside*; findings that require a fix
  route back to the coordinator via the question-router or a direct nudge, same as
  the V-5 router-hygiene note filed in `superbot-next` PR #30).
